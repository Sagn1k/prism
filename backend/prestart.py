"""Run before uvicorn starts — creates tables if they don't exist."""
import asyncio
from sqlalchemy import text
from app.database import engine, Base
import app.models  # noqa: F401 — register all models


CREATE_ENUM_SQL = """
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{name}') THEN
        CREATE TYPE {name} AS ENUM ({values});
    END IF;
END $$;
"""


async def init_db():
    enums = [
        ("user_role", "'student','counsellor','admin','parent'"),
        ("school_tier", "'starter','professional','premium'"),
        ("mission_type", "'flash','scenario_sim','build_quest','ai_debate','this_or_that'"),
        ("mission_difficulty", "'easy','medium','hard'"),
        ("attempt_status", "'in_progress','completed','abandoned'"),
        ("chosen_option", "'a','b'"),
        ("stream_fit", "'science','commerce','humanities','any'"),
    ]

    async with engine.begin() as conn:
        for name, values in enums:
            await conn.execute(text(CREATE_ENUM_SQL.format(name=name, values=values)))

        await conn.run_sync(Base.metadata.create_all, checkfirst=True)

    await engine.dispose()
    print("Database tables created successfully.")


if __name__ == "__main__":
    asyncio.run(init_db())
