"""
Main server module for MCP OAuth Dynamic Client
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth_authlib import AuthManager
from .config import Settings
from .redis_client import RedisManager
from .routes import create_oauth_router


def create_app(settings: Settings = None) -> FastAPI:
    """Create and configure the FastAPI application"""

    if settings is None:
        settings = Settings()

    # Initialize managers
    redis_manager = RedisManager(settings)
    auth_manager = AuthManager(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Manage application lifecycle"""
        # Startup
        await redis_manager.initialize()
        yield
        # Shutdown
        await redis_manager.close()

    # Create FastAPI app
    app = FastAPI(
        title="MCP OAuth Gateway - Auth Service",
        description="Sacred Auth Service following OAuth 2.1 and RFC 7591 divine specifications",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Configure CORS
    cors_origins = os.getenv("MCP_CORS_ORIGINS", "").split(",")
    cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]

    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["X-User-Id", "X-User-Name", "X-Auth-Token"],
        )

    # Include OAuth routes with Authlib ResourceProtector for enhanced security
    oauth_router = create_oauth_router(settings, redis_manager, auth_manager)
    app.include_router(oauth_router)

    return app


# Create a default app instance for uvicorn
app = create_app()
