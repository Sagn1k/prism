"""Identity Engine — core trait scoring and spectrum management."""

import logging
import math
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.game import MissionAttempt, TotResponse
from app.models.spectrum import Archetype, Spectrum, SpectrumHistory

logger = logging.getLogger(__name__)

DIMENSIONS = [
    "analytical_creative",
    "builder_explorer",
    "leader_specialist",
    "entrepreneur_steward",
    "people_systems",
]

# Color mapping: dimension -> color name
DIMENSION_COLORS = {
    "analytical_creative": ("Violet", "Magenta"),  # negative=Violet, positive=Magenta
    "builder_explorer": ("Amber", "Cyan"),  # negative=Amber, positive=Cyan
    "people_systems": ("Green", "Green"),  # both ends contribute Green
}

BASE_LEARNING_RATE = 0.3
MIN_LEARNING_RATE = 0.05


def _learning_rate(total_signals: int) -> float:
    """Decaying learning rate: starts at 0.3, decays toward 0.05."""
    if total_signals <= 0:
        return BASE_LEARNING_RATE
    decay = max(MIN_LEARNING_RATE, BASE_LEARNING_RATE / math.log2(total_signals + 2))
    return decay


def _decay_factor(total_signals: int) -> float:
    """Decay factor = 1 / log2(total_signals + 2)."""
    return 1.0 / math.log2(total_signals + 2)


def _clamp(value: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a)) or 1e-9
    mag_b = math.sqrt(sum(b * b for b in vec_b)) or 1e-9
    return dot / (mag_a * mag_b)


async def _get_or_create_spectrum(db: AsyncSession, user_id: uuid.UUID) -> Spectrum:
    """Fetch or initialize a user's spectrum."""
    result = await db.execute(
        select(Spectrum).where(Spectrum.user_id == user_id)
    )
    spectrum = result.scalar_one_or_none()
    if spectrum is None:
        spectrum = Spectrum(
            user_id=user_id,
            analytical_creative=0.0,
            builder_explorer=0.0,
            leader_specialist=0.0,
            entrepreneur_steward=0.0,
            people_systems=0.0,
            total_signals=0,
            color_ratios={},
        )
        db.add(spectrum)
        await db.flush()
    return spectrum


async def process_signal(
    db: AsyncSession,
    user_id: uuid.UUID,
    signals: dict[str, float],
    source: str,
) -> Spectrum:
    """
    Update spectrum dimensions from incoming trait signals.

    Formula: new_value = old_value + (signal_strength * learning_rate * decay_factor)
    Values are clamped to [-1, 1].
    """
    spectrum = await _get_or_create_spectrum(db, user_id)
    total = spectrum.total_signals or 0
    lr = _learning_rate(total)
    df = _decay_factor(total)

    for dim in DIMENSIONS:
        if dim not in signals:
            continue
        old_value = getattr(spectrum, dim) or 0.0
        signal_strength = signals[dim]
        new_value = old_value + (signal_strength * lr * df)
        setattr(spectrum, dim, _clamp(new_value))

    signal_count = len([d for d in DIMENSIONS if d in signals])
    spectrum.total_signals = total + max(signal_count, 1)

    logger.info(
        "Processed %d signals for user %s from %s (total_signals=%d)",
        signal_count,
        user_id,
        source,
        spectrum.total_signals,
    )
    return spectrum


async def update_archetype(db: AsyncSession, spectrum: Spectrum) -> Spectrum:
    """
    Compute cosine similarity between spectrum and each archetype's ideal center.
    Apply hysteresis: only change primary if new best exceeds current by 0.1.
    """
    result = await db.execute(
        select(Archetype).where(Archetype.is_active.is_(True))
    )
    archetypes = result.scalars().all()
    if not archetypes:
        logger.warning("No active archetypes found, skipping update")
        return spectrum

    spectrum_vec = [getattr(spectrum, dim) or 0.0 for dim in DIMENSIONS]

    scores: list[tuple[float, Archetype]] = []
    for arch in archetypes:
        # trait_ranges can be {dim: [min, max]} or {dim: float}
        center = arch.trait_ranges or {}
        arch_vec = []
        for dim in DIMENSIONS:
            val = center.get(dim, 0.0)
            if isinstance(val, (list, tuple)) and len(val) == 2:
                arch_vec.append((val[0] + val[1]) / 2.0)  # midpoint
            elif isinstance(val, (int, float)):
                arch_vec.append(float(val))
            else:
                arch_vec.append(0.0)
        sim = _cosine_similarity(spectrum_vec, arch_vec)
        scores.append((sim, arch))

    scores.sort(key=lambda x: x[0], reverse=True)
    best_score, best_arch = scores[0]

    # Hysteresis: only switch if new best exceeds current by 0.1
    current_score = 0.0
    if spectrum.primary_archetype_id:
        for score, arch in scores:
            if arch.id == spectrum.primary_archetype_id:
                current_score = score
                break

    HYSTERESIS_THRESHOLD = 0.1
    if (
        spectrum.primary_archetype_id is None
        or best_score > current_score + HYSTERESIS_THRESHOLD
    ):
        spectrum.primary_archetype_id = best_arch.id
        logger.info(
            "Updated primary archetype to %s (score=%.3f)",
            best_arch.label,
            best_score,
        )

    # Secondary archetype: best that isn't the primary
    for score, arch in scores:
        if arch.id != spectrum.primary_archetype_id:
            spectrum.secondary_archetype_id = arch.id
            break

    spectrum.confidence_score = best_score
    return spectrum


def calculate_color_ratios(spectrum: Spectrum) -> dict[str, float]:
    """
    Map dimensions to Prism colors and normalize to sum=1.0.

    Mapping:
      analytical (negative analytical_creative) -> Violet
      creative (positive analytical_creative) -> Magenta
      builder (negative builder_explorer) -> Amber
      explorer (positive builder_explorer) -> Cyan
      people/systems -> Green
    """
    ac = getattr(spectrum, "analytical_creative", 0.0) or 0.0
    be = getattr(spectrum, "builder_explorer", 0.0) or 0.0
    ps = getattr(spectrum, "people_systems", 0.0) or 0.0

    # Raw color strengths (use absolute deviations)
    raw = {
        "Violet": max(0.0, -ac),      # analytical end
        "Magenta": max(0.0, ac),       # creative end
        "Amber": max(0.0, -be),        # builder end
        "Cyan": max(0.0, be),          # explorer end
        "Green": abs(ps),              # people/systems presence
    }

    total = sum(raw.values())
    if total < 1e-9:
        # Equal distribution when no signal
        return {k: 1.0 / len(raw) for k in raw}

    return {k: v / total for k, v in raw.items()}


async def recalculate_spectrum(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> Spectrum:
    """
    Full spectrum recalculation pipeline:
    1. Get current spectrum (signals already applied)
    2. Update archetype assignment
    3. Update color ratios
    4. Save history snapshot
    """
    spectrum = await _get_or_create_spectrum(db, user_id)

    # Update archetype
    spectrum = await update_archetype(db, spectrum)

    # Update colors
    spectrum.color_ratios = calculate_color_ratios(spectrum)

    # Save snapshot
    snapshot = SpectrumHistory(
        spectrum_id=spectrum.id,
        dimension_snapshot={dim: getattr(spectrum, dim) or 0.0 for dim in DIMENSIONS},
        archetype_label=None,
        confidence=spectrum.confidence_score,
        trigger_event="recalculate",
        recorded_at=datetime.now(timezone.utc),
    )

    # Resolve archetype label
    if spectrum.primary_archetype_id:
        arch_result = await db.execute(
            select(Archetype).where(Archetype.id == spectrum.primary_archetype_id)
        )
        primary = arch_result.scalar_one_or_none()
        if primary:
            snapshot.archetype_label = primary.label

    db.add(snapshot)
    await db.flush()

    logger.info("Recalculated spectrum for user %s", user_id)
    return spectrum


async def process_mission_signals(
    db: AsyncSession,
    user_id: uuid.UUID,
    attempt: MissionAttempt,
) -> Spectrum:
    """
    Extract trait signals from a completed mission attempt.

    Uses the mission's trait_weights combined with the attempt's scores
    to produce dimension signals.
    """
    # Load mission with trait_weights
    await db.refresh(attempt, ["mission"])
    mission = attempt.mission
    if not mission or not mission.trait_weights:
        logger.warning("Mission %s has no trait_weights, skipping", attempt.mission_id)
        spectrum = await _get_or_create_spectrum(db, user_id)
        return spectrum

    trait_weights: dict = mission.trait_weights
    scores = attempt.scores or {}

    # trait_weights can be flat: {"analytical_creative": 0.7, ...}
    # or nested per score key: {"accuracy": {"analytical_creative": 0.7}, ...}
    signals: dict[str, float] = {}

    # Check if it's flat (keys are dimension names)
    is_flat = any(k in DIMENSIONS for k in trait_weights)

    if is_flat:
        # Flat format: use average score as multiplier
        avg_score = sum(
            v for v in scores.values() if isinstance(v, (int, float))
        ) / max(len(scores), 1)
        for dim in DIMENSIONS:
            weight = trait_weights.get(dim)
            if weight and isinstance(weight, (int, float)):
                signals[dim] = weight * avg_score
    else:
        # Nested format: per score key
        for score_key, score_value in scores.items():
            if not isinstance(score_value, (int, float)):
                continue
            weights_for_score = trait_weights.get(score_key, {})
            if isinstance(weights_for_score, dict):
                for dim, weight in weights_for_score.items():
                    if dim in DIMENSIONS:
                        signals[dim] = signals.get(dim, 0.0) + score_value * weight

    # Also factor in standard scores
    for attr, dim_map in [
        ("creativity_score", {"analytical_creative": 1.0}),
        ("accuracy_score", {"analytical_creative": -0.5}),
    ]:
        val = getattr(attempt, attr, None)
        if val is not None:
            for dim, w in dim_map.items():
                signals[dim] = signals.get(dim, 0.0) + val * w * 0.3

    spectrum = await process_signal(db, user_id, signals, source=f"mission:{mission.id}")
    spectrum = await recalculate_spectrum(db, user_id)
    return spectrum


async def process_tot_signals(
    db: AsyncSession,
    user_id: uuid.UUID,
    responses: list[TotResponse],
) -> Spectrum:
    """
    Extract trait signals from This-or-That responses.

    Each question has trait_weights_a and trait_weights_b;
    the chosen option determines which weights are applied.
    """
    aggregated: dict[str, float] = {}

    for resp in responses:
        await db.refresh(resp, ["question"])
        question = resp.question
        if not question:
            continue

        if resp.chosen_option.value == "a":
            weights = question.trait_weights_a or {}
        else:
            weights = question.trait_weights_b or {}

        for dim, value in weights.items():
            if dim in DIMENSIONS:
                aggregated[dim] = aggregated.get(dim, 0.0) + float(value)

    if aggregated:
        spectrum = await process_signal(
            db, user_id, aggregated, source="this_or_that"
        )
        spectrum = await recalculate_spectrum(db, user_id)
        return spectrum

    return await _get_or_create_spectrum(db, user_id)
