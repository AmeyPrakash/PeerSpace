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

from contextlib import asynccontextmanager

logger = logging.getLogger("peerspace.app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database tables exist on Neon / PostgreSQL
    try:
        from backend.database import init_db
        await init_db()
        logger.info("PeerSpace database schema initialized and verified.")
    except Exception as e:
        logger.warning(f"Database auto-initialization skipped or failed: {e}")
    yield

def create_app() -> FastAPI:
    """Factory function initializing the PeerSpace FastAPI application."""
    app = FastAPI(
        title="PeerSpace API",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan
    )

    # Attach Security Middleware
    app.middleware("http")(add_security_headers)

    # Health Check Endpoint with Database Connectivity Verification
    @app.get("/api/health", tags=["system"])
    async def health_check():
        """
        Verifies API and database connectivity without exposing credentials or internal errors.
        """
        db_status = "connected"
        overall_status = "healthy"
        http_code = 200

        try:
            from sqlalchemy import text
            from backend.database import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1"))
                if result.scalar() != 1:
                    db_status = "degraded"
                    overall_status = "degraded"
                    http_code = 503
        except Exception as e:
            # Log failure internally without exposing credentials or stack traces to client
            logger.error("Database health check failed: %s", type(e).__name__)
            db_status = "disconnected"
            overall_status = "degraded"
            http_code = 503

        return JSONResponse(
            status_code=http_code,
            content={
                "status": overall_status,
                "database": db_status,
                "service": "peerspace-api",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        )

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
