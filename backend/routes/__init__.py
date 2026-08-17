"""
PeerSpace Routes Package
"""

from backend.routes.auth_routes import router as auth_router
from backend.routes.chat_routes import router as chat_router
from backend.routes.admin_routes import router as admin_router
from backend.routes.voice_routes import router as voice_router

__all__ = ["auth_router", "chat_router", "admin_router", "voice_router"]
