"""Central exception handlers mapping domain errors to safe HTTP responses."""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.modules.auth.utils.exceptions import AuthError

logger = logging.getLogger("auth")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AuthError)
    async def _handle_auth_error(request: Request, exc: AuthError) -> JSONResponse:
        # Log server-side; return only a safe message + code to the client.
        logger.info("AuthError %s: %s", exc.code, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "code": exc.code},
        )
