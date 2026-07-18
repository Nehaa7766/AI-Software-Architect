"""HTTP handlers for the project scanner (Phase 3)."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.security import CurrentUser
from app.modules.projects.dependencies import get_project_service
from app.modules.projects.dto.responses import (
    FileListResponse,
    ProjectTreeResponse,
    ScanSummaryResponse,
)
from app.modules.projects.services.project_service import ProjectService
from app.modules.projects.views.file_view import FileView

router = APIRouter(prefix="/projects", tags=["projects"])

ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


@router.post("/{project_id}/scan", response_model=ScanSummaryResponse)
async def scan_project(
    project_id: str, current_user: CurrentUser, service: ProjectServiceDep
) -> ScanSummaryResponse:
    """Re-run the source-file scan and return the inventory summary."""
    total, by_language = await service.scan_project(
        project_id=project_id, owner_id=current_user.id
    )
    return FileView.summary(total, by_language)


@router.get("/{project_id}/tree", response_model=ProjectTreeResponse)
async def project_tree(
    project_id: str, current_user: CurrentUser, service: ProjectServiceDep
) -> ProjectTreeResponse:
    """Return the extracted project's full folder/file tree (for the explorer)."""
    tree = await service.get_file_tree(
        project_id=project_id, owner_id=current_user.id
    )
    return FileView.tree(tree)


@router.get("/{project_id}/files", response_model=FileListResponse)
async def list_files(
    project_id: str,
    current_user: CurrentUser,
    service: ProjectServiceDep,
    language: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> FileListResponse:
    """List a project's scanned source files (optionally filtered by language)."""
    files, total, by_language = await service.list_files(
        project_id=project_id,
        owner_id=current_user.id,
        language=language,
        limit=limit,
        offset=offset,
    )
    return FileView.collection(files, total, by_language)
