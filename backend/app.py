"""
PeerSpace Main Application Factory
Wires together FastAPI, middleware, routes, and static file serving.
"""

import time
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.config import FRONTEND_DIR
from backend.middleware import add_security_headers
from backend.routes.auth_routes import router as auth_router
from backend.routes.chat_routes import router as chat_router
from backend.routes.admin_routes import router as admin_router
from backend.routes.voice_routes import router as voice_router
from backend.routes.counselor_routes import router as counselor_router
from backend.routes.counselor_ws_routes import router as counselor_ws_router

logger = logging.getLogger("peerspace.app")

def create_app() -> FastAPI:
    """Factory function initializing the PeerSpace FastAPI application."""
    app = FastAPI(
        title="PeerSpace API",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None
    )

    # Attach Security Middleware
    app.middleware("http")(add_security_headers)

    # Health Check Endpoint
    @app.get("/api/health", tags=["system"])
    async def health_check():
        return {
            "status": "healthy",
            "service": "peerspace-api",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    # Register API Routers
    app.include_router(auth_router)
    app.include_router(chat_router)
    app.include_router(admin_router)
    app.include_router(voice_router)
    app.include_router(counselor_router)
    app.include_router(counselor_ws_router)

    # Static File Mounting
    if FRONTEND_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/", tags=["ui"])
    async def serve_ui():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return JSONResponse(status_code=404, content={"error": "UI not found"})

    return app

app = create_app()
