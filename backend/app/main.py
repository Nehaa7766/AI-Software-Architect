"""FastAPI application entrypoint for the AI Software Architect auth module."""
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.middleware import SecurityHeadersMiddleware
from app.core.rate_limit import limiter
from app.modules.analysis.middlewares.error_handlers import (
    register_exception_handlers as register_analysis_exception_handlers,
)
from app.modules.analysis.routes.analysis_routes import router as analysis_router
from app.modules.auth.middlewares.error_handlers import register_exception_handlers
from app.modules.auth.routes.auth_routes import router as auth_router
from app.modules.projects.middlewares.error_handlers import (
    register_exception_handlers as register_project_exception_handlers,
)
from app.modules.projects.routes.project_routes import router as projects_router

logging.basicConfig(level=logging.INFO)


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Software Architect API",
        version="0.1.0",
        description="Authentication module — register, login, Google OAuth, profiles.",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # CORS — explicit whitelist, credentials enabled for cookie auth.
    # In development also allow any localhost/127.0.0.1 port (the Next dev server
    # picks 3001+ when 3000 is taken), so preflight never fails locally.
    cors_kwargs: dict = {
        "allow_origins": settings.client_origins,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
        "expose_headers": ["X-CSRF-Token"],
    }
    if not settings.is_production:
        cors_kwargs["allow_origin_regex"] = (
            r"https?://(localhost|127\.0\.0\.1)(:\d+)?"
        )
    app.add_middleware(CORSMiddleware, **cors_kwargs)

    # Domain exception -> HTTP mapping
    register_exception_handlers(app)
    register_project_exception_handlers(app)
    register_analysis_exception_handlers(app)

    # Routers
    app.include_router(auth_router, prefix=settings.API_PREFIX)
    app.include_router(projects_router, prefix=settings.API_PREFIX)
    app.include_router(analysis_router, prefix=settings.API_PREFIX)

    # Serve uploaded files (e.g. avatars)
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

    # Workspace for imported projects (never served statically — code is not executed).
    Path(settings.WORKSPACE_DIR).mkdir(parents=True, exist_ok=True)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.ENVIRONMENT}

    return app


app = create_app()
