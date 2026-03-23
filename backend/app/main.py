from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
import app.models  # noqa: F401 — ensure all models are registered on Base.metadata


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    app.state.redis = aioredis.from_url(
        settings.REDIS_URL, decode_responses=True
    )
    yield
    # Shutdown
    await app.state.redis.close()
    await engine.dispose()


app = FastAPI(
    title="Prism API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|172\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# --- Routers ---
from app.routers import (
    auth_router,
    game_router,
    identity_router,
    ai_router,
    careers_router,
    cards_router,
    school_router,
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(game_router, prefix="/api/v1")
app.include_router(identity_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(careers_router, prefix="/api/v1")
app.include_router(cards_router, prefix="/api/v1")
app.include_router(school_router, prefix="/api/v1")
