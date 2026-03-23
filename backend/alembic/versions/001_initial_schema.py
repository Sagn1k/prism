"""initial schema

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-03-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable uuid-ossp extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # --- Enum types ---
    user_role = postgresql.ENUM("student", "counsellor", "admin", "parent", name="user_role", create_type=False)
    user_role.create(op.get_bind(), checkfirst=True)

    school_tier = postgresql.ENUM("starter", "professional", "premium", name="school_tier", create_type=False)
    school_tier.create(op.get_bind(), checkfirst=True)

    mission_type = postgresql.ENUM("flash", "scenario_sim", "build_quest", "ai_debate", "this_or_that", name="mission_type", create_type=False)
    mission_type.create(op.get_bind(), checkfirst=True)

    mission_difficulty = postgresql.ENUM("easy", "medium", "hard", name="mission_difficulty", create_type=False)
    mission_difficulty.create(op.get_bind(), checkfirst=True)

    attempt_status = postgresql.ENUM("in_progress", "completed", "abandoned", name="attempt_status", create_type=False)
    attempt_status.create(op.get_bind(), checkfirst=True)

    chosen_option = postgresql.ENUM("a", "b", name="chosen_option", create_type=False)
    chosen_option.create(op.get_bind(), checkfirst=True)

    stream_fit = postgresql.ENUM("science", "commerce", "humanities", "any", name="stream_fit", create_type=False)
    stream_fit.create(op.get_bind(), checkfirst=True)

    conversation_role = postgresql.ENUM("user", "assistant", "system", name="conversation_role", create_type=False)
    conversation_role.create(op.get_bind(), checkfirst=True)

    # --- schools ---
    op.create_table(
        "schools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("cbse_affiliation_no", sa.String(50), unique=True, nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("tier", sa.Enum("starter", "professional", "premium", name="school_tier", create_type=False), nullable=False),
        sa.Column("plan_type", sa.String(50), nullable=True),
        sa.Column("student_limit", sa.Integer(), nullable=True),
        sa.Column("subscription_start", sa.Date(), nullable=True),
        sa.Column("subscription_end", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schools.id"), nullable=True),
        sa.Column("phone", sa.String(20), unique=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("student", "counsellor", "admin", "parent", name="user_role", create_type=False), nullable=False),
        sa.Column("avatar_url", sa.String(512), nullable=True),
        sa.Column("xp_points", sa.Integer(), server_default="0", nullable=False),
        sa.Column("level", sa.Integer(), server_default="1", nullable=False),
        sa.Column("current_archetype_label", sa.String(100), nullable=True),
        sa.Column("onboarded", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- classes ---
    op.create_table(
        "classes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("grade", sa.String(10), nullable=False),
        sa.Column("section", sa.String(10), nullable=True),
        sa.Column("stream", sa.String(50), nullable=True),
        sa.Column("academic_year", sa.String(9), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- class_students ---
    op.create_table(
        "class_students",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("classes.id"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- archetypes ---
    op.create_table(
        "archetypes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("emoji_icon", sa.String(10), nullable=True),
        sa.Column("trait_ranges", postgresql.JSONB(), nullable=True),
        sa.Column("color_weights", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- spectrums ---
    op.create_table(
        "spectrums",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("analytical_creative", sa.Float(), nullable=True),
        sa.Column("builder_explorer", sa.Float(), nullable=True),
        sa.Column("leader_specialist", sa.Float(), nullable=True),
        sa.Column("entrepreneur_steward", sa.Float(), nullable=True),
        sa.Column("people_systems", sa.Float(), nullable=True),
        sa.Column("primary_archetype_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("archetypes.id"), nullable=True),
        sa.Column("secondary_archetype_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("archetypes.id"), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("color_ratios", postgresql.JSONB(), nullable=True),
        sa.Column("total_signals", sa.Integer(), server_default="0", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- spectrum_history ---
    op.create_table(
        "spectrum_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("spectrum_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("spectrums.id"), nullable=False),
        sa.Column("dimension_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("archetype_label", sa.String(100), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("trigger_event", sa.String(255), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- worlds ---
    op.create_table(
        "worlds",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("color_hex", sa.String(7), nullable=True),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("icon_url", sa.String(512), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- missions ---
    op.create_table(
        "missions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("world_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("worlds.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("type", sa.Enum("flash", "scenario_sim", "build_quest", "ai_debate", "this_or_that", name="mission_type", create_type=False), nullable=False),
        sa.Column("difficulty", sa.Enum("easy", "medium", "hard", name="mission_difficulty", create_type=False), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("content_payload", postgresql.JSONB(), nullable=True),
        sa.Column("scoring_rubric", postgresql.JSONB(), nullable=True),
        sa.Column("trait_weights", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- mission_attempts ---
    op.create_table(
        "mission_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("missions.id"), nullable=False),
        sa.Column("responses", postgresql.JSONB(), nullable=True),
        sa.Column("scores", postgresql.JSONB(), nullable=True),
        sa.Column("creativity_score", sa.Float(), nullable=True),
        sa.Column("speed_score", sa.Float(), nullable=True),
        sa.Column("accuracy_score", sa.Float(), nullable=True),
        sa.Column("xp_earned", sa.Integer(), server_default="0", nullable=False),
        sa.Column("time_spent_sec", sa.Integer(), nullable=True),
        sa.Column("status", sa.Enum("in_progress", "completed", "abandoned", name="attempt_status", create_type=False), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- tot_questions ---
    op.create_table(
        "tot_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("question_text", sa.String(1000), nullable=False),
        sa.Column("option_a", sa.String(500), nullable=False),
        sa.Column("option_b", sa.String(500), nullable=False),
        sa.Column("trait_weights_a", postgresql.JSONB(), nullable=True),
        sa.Column("trait_weights_b", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- tot_responses ---
    op.create_table(
        "tot_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tot_questions.id"), nullable=False),
        sa.Column("chosen_option", sa.Enum("a", "b", name="chosen_option", create_type=False), nullable=False),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- badges ---
    op.create_table(
        "badges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("icon_url", sa.String(512), nullable=True),
        sa.Column("unlock_criteria", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- user_badges ---
    op.create_table(
        "user_badges",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("badge_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("badges.id"), primary_key=True),
        sa.Column("earned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- streaks ---
    op.create_table(
        "streaks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("current_streak", sa.Integer(), server_default="0", nullable=False),
        sa.Column("longest_streak", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_activity_date", sa.Date(), nullable=True),
    )

    # --- daily_quests ---
    op.create_table(
        "daily_quests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("missions.id"), nullable=False),
        sa.Column("quest_date", sa.Date(), nullable=False),
        sa.Column("is_completed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- careers ---
    op.create_table(
        "careers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), unique=True, nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("stream_fit", sa.Enum("science", "commerce", "humanities", "any", name="stream_fit", create_type=False), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("salary_range", postgresql.JSONB(), nullable=True),
        sa.Column("entry_paths", postgresql.JSONB(), nullable=True),
        sa.Column("required_exams", postgresql.JSONB(), nullable=True),
        sa.Column("college_options", postgresql.JSONB(), nullable=True),
        sa.Column("day_in_life", postgresql.JSONB(), nullable=True),
        sa.Column("archetype_fit_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- career_bookmarks ---
    op.create_table(
        "career_bookmarks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("career_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("careers.id"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- prism_cards ---
    op.create_table(
        "prism_cards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("card_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("card_data", postgresql.JSONB(), nullable=True),
        sa.Column("image_url", sa.String(512), nullable=True),
        sa.Column("share_token", sa.String(255), unique=True, nullable=True),
        sa.Column("is_public", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- ai_conversations ---
    op.create_table(
        "ai_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_id", sa.String(255), index=True, nullable=False),
        sa.Column("role", sa.Enum("user", "assistant", "system", name="conversation_role", create_type=False), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("context_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- otp_tokens ---
    op.create_table(
        "otp_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("phone", sa.String(20), index=True, nullable=False),
        sa.Column("otp_code", sa.String(10), nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_used", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- parent_reports ---
    op.create_table(
        "parent_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("report_data", postgresql.JSONB(), nullable=True),
        sa.Column("pdf_url", sa.String(512), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- Custom indexes ---
    op.create_index("idx_users_school_role", "users", ["school_id", "role"])
    op.create_index("idx_users_phone", "users", ["phone"])

    op.create_index(
        "idx_mission_attempts_user",
        "mission_attempts",
        ["user_id", sa.text("completed_at DESC")],
    )

    op.create_index(
        "idx_spectrum_history_spectrum",
        "spectrum_history",
        ["spectrum_id", sa.text("recorded_at DESC")],
    )

    op.create_index(
        "idx_ai_conversations_session",
        "ai_conversations",
        ["session_id", "created_at"],
    )

    op.create_index(
        "idx_prism_cards_share",
        "prism_cards",
        ["share_token"],
        postgresql_where=sa.text("is_public = true"),
    )

    op.create_index(
        "idx_daily_quests_user_date",
        "daily_quests",
        ["user_id", "quest_date"],
    )

    op.create_index(
        "idx_careers_stream",
        "careers",
        ["stream_fit"],
        postgresql_where=sa.text("is_active = true"),
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_careers_stream", table_name="careers")
    op.drop_index("idx_daily_quests_user_date", table_name="daily_quests")
    op.drop_index("idx_prism_cards_share", table_name="prism_cards")
    op.drop_index("idx_ai_conversations_session", table_name="ai_conversations")
    op.drop_index("idx_spectrum_history_spectrum", table_name="spectrum_history")
    op.drop_index("idx_mission_attempts_user", table_name="mission_attempts")
    op.drop_index("idx_users_phone", table_name="users")
    op.drop_index("idx_users_school_role", table_name="users")

    # Drop tables in reverse dependency order
    op.drop_table("parent_reports")
    op.drop_table("otp_tokens")
    op.drop_table("ai_conversations")
    op.drop_table("prism_cards")
    op.drop_table("career_bookmarks")
    op.drop_table("careers")
    op.drop_table("daily_quests")
    op.drop_table("streaks")
    op.drop_table("user_badges")
    op.drop_table("badges")
    op.drop_table("tot_responses")
    op.drop_table("tot_questions")
    op.drop_table("mission_attempts")
    op.drop_table("missions")
    op.drop_table("worlds")
    op.drop_table("spectrum_history")
    op.drop_table("spectrums")
    op.drop_table("archetypes")
    op.drop_table("class_students")
    op.drop_table("classes")
    op.drop_table("users")
    op.drop_table("schools")

    # Drop enum types
    sa.Enum(name="conversation_role").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="stream_fit").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="chosen_option").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="attempt_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="mission_difficulty").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="mission_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="school_tier").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)

    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
