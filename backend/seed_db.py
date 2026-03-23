"""
Seed database script for Prism.

Loads all seed data from the /seed directory into the database.

Usage:
    cd backend
    python seed_db.py
"""

import json
import sys
import uuid
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Ensure the backend package is on the path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import get_settings
from app.database import Base
from app.models.spectrum import Archetype
from app.models.game import World, Mission, TotQuestion
from app.models.career import Career

SEED_DIR = Path(__file__).parent.parent / "seed"

settings = get_settings()
SYNC_DATABASE_URL = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
engine = create_engine(SYNC_DATABASE_URL, echo=False)


def load_json(filename: str) -> list[dict]:
    filepath = SEED_DIR / filename
    if not filepath.exists():
        print(f"  WARNING: {filepath} not found, skipping.")
        return []
    with open(filepath) as f:
        return json.load(f)


def seed_archetypes(session: Session) -> dict[str, uuid.UUID]:
    """Seed archetypes and return a name->id mapping."""
    data = load_json("archetypes.json")
    if not data:
        return {}

    name_to_id: dict[str, uuid.UUID] = {}

    for item in data:
        existing = session.execute(
            select(Archetype).where(Archetype.name == item["name"])
        ).scalar_one_or_none()

        if existing:
            print(f"  Archetype '{item['name']}' already exists, skipping.")
            name_to_id[item["name"]] = existing.id
            continue

        archetype = Archetype(
            id=uuid.uuid4(),
            name=item["name"],
            label=item["label"],
            description=item.get("description"),
            emoji_icon=item.get("emoji_icon"),
            trait_ranges=item.get("trait_ranges"),
            color_weights=item.get("color_weights"),
        )
        session.add(archetype)
        name_to_id[item["name"]] = archetype.id
        print(f"  + Archetype: {item['label']}")

    session.flush()
    return name_to_id


def seed_worlds(session: Session) -> dict[str, uuid.UUID]:
    """Seed worlds and return a slug->id mapping."""
    data = load_json("worlds.json")
    if not data:
        return {}

    slug_to_id: dict[str, uuid.UUID] = {}

    for item in data:
        existing = session.execute(
            select(World).where(World.slug == item["slug"])
        ).scalar_one_or_none()

        if existing:
            print(f"  World '{item['name']}' already exists, skipping.")
            slug_to_id[item["slug"]] = existing.id
            continue

        world = World(
            id=uuid.uuid4(),
            name=item["name"],
            slug=item["slug"],
            color_hex=item.get("color_hex"),
            description=item.get("description"),
            icon_url=item.get("icon_url"),
            sort_order=item.get("sort_order", 0),
        )
        session.add(world)
        slug_to_id[item["slug"]] = world.id
        print(f"  + World: {item['name']}")

    session.flush()
    return slug_to_id


def seed_missions(session: Session, world_slugs: dict[str, uuid.UUID]) -> None:
    """Seed missions, linking to worlds by slug."""
    data = load_json("missions.json")
    if not data:
        return

    for item in data:
        world_slug = item.get("world_slug")
        world_id = world_slugs.get(world_slug)

        if not world_id:
            # Try to look up from DB
            world = session.execute(
                select(World).where(World.slug == world_slug)
            ).scalar_one_or_none()
            if world:
                world_id = world.id
            else:
                print(f"  WARNING: World '{world_slug}' not found, skipping mission '{item['title']}'")
                continue

        # Check for duplicate by title + world
        existing = session.execute(
            select(Mission).where(
                Mission.title == item["title"],
                Mission.world_id == world_id,
            )
        ).scalar_one_or_none()

        if existing:
            print(f"  Mission '{item['title']}' already exists, skipping.")
            continue

        mission = Mission(
            id=uuid.uuid4(),
            world_id=world_id,
            title=item["title"],
            type=item["type"],
            difficulty=item["difficulty"],
            duration_seconds=item.get("duration_seconds"),
            content_payload=item.get("content_payload"),
            scoring_rubric=item.get("scoring_rubric"),
            trait_weights=item.get("trait_weights"),
            sort_order=item.get("sort_order", 0),
        )
        session.add(mission)
        print(f"  + Mission: {item['title']} ({world_slug})")

    session.flush()


def seed_tot_questions(session: Session) -> None:
    """Seed This-or-That questions."""
    data = load_json("tot_questions.json")
    if not data:
        return

    for item in data:
        existing = session.execute(
            select(TotQuestion).where(
                TotQuestion.question_text == item["question_text"]
            )
        ).scalar_one_or_none()

        if existing:
            print(f"  ToT question already exists, skipping: '{item['question_text'][:50]}...'")
            continue

        question = TotQuestion(
            id=uuid.uuid4(),
            question_text=item["question_text"],
            option_a=item["option_a"],
            option_b=item["option_b"],
            trait_weights_a=item.get("trait_weights_a"),
            trait_weights_b=item.get("trait_weights_b"),
        )
        session.add(question)
        print(f"  + ToT: {item['question_text'][:60]}...")

    session.flush()


def seed_careers(session: Session, archetype_names: dict[str, uuid.UUID]) -> None:
    """Seed careers with Indian context."""
    data = load_json("careers.json")
    if not data:
        return

    for item in data:
        existing = session.execute(
            select(Career).where(Career.slug == item["slug"])
        ).scalar_one_or_none()

        if existing:
            print(f"  Career '{item['title']}' already exists, skipping.")
            continue

        # Resolve archetype_fit names to UUIDs
        archetype_fit_ids = None
        if item.get("archetype_fit"):
            archetype_fit_ids = [
                archetype_names[name]
                for name in item["archetype_fit"]
                if name in archetype_names
            ]

        career = Career(
            id=uuid.uuid4(),
            title=item["title"],
            slug=item["slug"],
            category=item.get("category"),
            stream_fit=item["stream_fit"],
            description=item.get("description"),
            salary_range=item.get("salary_range"),
            entry_paths=item.get("entry_paths"),
            required_exams=item.get("required_exams"),
            college_options=item.get("college_options"),
            day_in_life=item.get("day_in_life"),
            archetype_fit_ids=archetype_fit_ids if archetype_fit_ids else None,
        )
        session.add(career)
        print(f"  + Career: {item['title']}")

    session.flush()


def main():
    print("=" * 60)
    print("Prism Database Seeder")
    print("=" * 60)
    print(f"Database: {SYNC_DATABASE_URL.split('@')[-1] if '@' in SYNC_DATABASE_URL else 'local'}")
    print()

    with Session(engine) as session:
        try:
            print("[1/5] Seeding archetypes...")
            archetype_names = seed_archetypes(session)
            print(f"       {len(archetype_names)} archetypes processed.\n")

            print("[2/5] Seeding worlds...")
            world_slugs = seed_worlds(session)
            print(f"       {len(world_slugs)} worlds processed.\n")

            print("[3/5] Seeding missions...")
            seed_missions(session, world_slugs)
            print()

            print("[4/5] Seeding This-or-That questions...")
            seed_tot_questions(session)
            print()

            print("[5/5] Seeding careers...")
            seed_careers(session, archetype_names)
            print()

            session.commit()
            print("=" * 60)
            print("Seed complete!")
            print("=" * 60)

        except Exception as e:
            session.rollback()
            print(f"\nERROR: {e}")
            raise


if __name__ == "__main__":
    main()
