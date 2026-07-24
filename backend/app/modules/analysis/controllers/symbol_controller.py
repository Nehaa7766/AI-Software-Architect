"""HTTP handlers for AST parsing + symbol retrieval (Phase 4)."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.security import CurrentUser
from app.models.symbol import SymbolType
from app.modules.analysis.dependencies import get_symbol_service
from app.modules.analysis.dto.responses import (
    ParseSummaryResponse,
    SymbolListResponse,
    SymbolsByFileResponse,
    SymbolSummaryResponse,
)
from app.modules.analysis.services.symbol_service import SymbolService
from app.modules.analysis.views.symbol_view import SymbolView

router = APIRouter(prefix="/projects", tags=["analysis"])

SymbolServiceDep = Annotated[SymbolService, Depends(get_symbol_service)]


@router.post("/{project_id}/parse", response_model=ParseSummaryResponse)
async def parse_project(
    project_id: str, current_user: CurrentUser, service: SymbolServiceDep
) -> ParseSummaryResponse:
    """Statically parse all supported files and (re)build the symbol table."""
    stats = await service.parse_project(
        project_id=project_id, owner_id=current_user.id
    )
    return SymbolView.summary(project_id, stats)


@router.get("/{project_id}/symbols", response_model=SymbolListResponse)
async def list_symbols(
    project_id: str,
    current_user: CurrentUser,
    service: SymbolServiceDep,
    q: Annotated[
        str | None,
        Query(description="Ranked name search; omit to list in file order."),
    ] = None,
    symbol_type: Annotated[SymbolType | None, Query()] = None,
    language: Annotated[str | None, Query()] = None,
    file_id: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SymbolListResponse:
    """Search (``q``) or list a project's extracted symbols (optionally filtered)."""
    items, total, by_type = await service.list_symbols(
        project_id=project_id,
        owner_id=current_user.id,
        q=q,
        symbol_type=symbol_type,
        language=language,
        file_id=file_id,
        limit=limit,
        offset=offset,
    )
    return SymbolView.collection(items, total, by_type)


@router.get("/{project_id}/symbols/by-file", response_model=SymbolsByFileResponse)
async def symbols_by_file(
    project_id: str, current_user: CurrentUser, service: SymbolServiceDep
) -> SymbolsByFileResponse:
    """Per-file symbol counts (functions/methods/classes) keyed by file path."""
    files, total = await service.counts_by_file(
        project_id=project_id, owner_id=current_user.id
    )
    return SymbolView.by_file(project_id, files, total)


@router.get("/{project_id}/symbols/summary", response_model=SymbolSummaryResponse)
async def symbol_summary(
    project_id: str, current_user: CurrentUser, service: SymbolServiceDep
) -> SymbolSummaryResponse:
    """Return aggregate symbol counts for a parsed project."""
    files_parsed, total, by_type = await service.get_summary(
        project_id=project_id, owner_id=current_user.id
    )
    return SymbolView.project_summary(project_id, files_parsed, total, by_type)
