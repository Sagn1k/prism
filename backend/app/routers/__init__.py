from app.routers.auth import router as auth_router
from app.routers.game import router as game_router
from app.routers.identity import router as identity_router
from app.routers.ai import router as ai_router
from app.routers.careers import router as careers_router
from app.routers.cards import router as cards_router
from app.routers.school import router as school_router

__all__ = [
    "auth_router",
    "game_router",
    "identity_router",
    "ai_router",
    "careers_router",
    "cards_router",
    "school_router",
]
