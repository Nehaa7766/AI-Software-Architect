"""HTTP handler for the read-only file viewer (Phase 5.1).

Thin: it never touches the filesystem — ownership, path safety and reading all
happen in :class:`FileViewerService`.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.security import CurrentUser
from app.modules.analysis.dependencies import get_file_viewer_service
from app.modules.analysis.dto.responses import FileContentResponse
from app.modules.analysis.services.file_viewer_service import FileViewerService

router = APIRouter(prefix="/projects", tags=["analysis"])

FileViewerServiceDep = Annotated[
    FileViewerService, Depends(get_file_viewer_service)
]


@router.get("/{project_id}/file", response_model=FileContentResponse)
async def read_file(
    project_id: str,
    current_user: CurrentUser,
    service: FileViewerServiceDep,
    path: Annotated[
        str,
        Query(description="Workspace-relative file path, e.g. app/main.py"),
    ],
) -> FileContentResponse:
    """Return a single source file's text for the read-only viewer."""
    result = await service.read_file(
        project_id=project_id, owner_id=current_user.id, rel_path=path
    )
    return FileContentResponse(
        path=result.path, language=result.language, content=result.content
    )
