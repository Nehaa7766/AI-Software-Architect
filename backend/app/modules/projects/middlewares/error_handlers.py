"""Central exception handler mapping ProjectError to safe HTTP responses."""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.modules.projects.utils.exceptions import ProjectError

logger = logging.getLogger("projects")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProjectError)
    async def _handle_project_error(request: Request, exc: ProjectError) -> JSONResponse:
        logger.info("ProjectError %s: %s", exc.code, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "code": exc.code},
        )
