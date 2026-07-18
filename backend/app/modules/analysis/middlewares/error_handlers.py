"""Central exception handler mapping AnalysisError to safe HTTP responses."""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.modules.analysis.utils.exceptions import AnalysisError

logger = logging.getLogger("analysis")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AnalysisError)
    async def _handle_analysis_error(
        request: Request, exc: AnalysisError
    ) -> JSONResponse:
        logger.info("AnalysisError %s: %s", exc.code, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "code": exc.code},
        )
