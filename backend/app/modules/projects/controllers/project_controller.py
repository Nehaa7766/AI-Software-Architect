"""HTTP handlers for project import endpoints (Phase 1)."""
from typing import Annotated

from fastapi import APIRouter, Depends, File, Request, UploadFile, status

from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security import CurrentUser
from app.modules.projects.dependencies import get_project_service
from app.modules.projects.dto.responses import (
    MessageResponse,
    ProjectListResponse,
    ProjectResponse,
)
from app.modules.projects.services.project_service import ProjectService
from app.modules.projects.validators.schemas import GitHubImportRequest
from app.modules.projects.views.project_view import ProjectView

router = APIRouter(prefix="/projects", tags=["projects"])

ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


@router.post("/upload", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_IMPORT)
async def upload_project(
    request: Request,
    current_user: CurrentUser,
    service: ProjectServiceDep,
    file: Annotated[UploadFile, File(...)],
) -> ProjectResponse:
    project = await service.import_zip(owner_id=current_user.id, upload=file)
    return ProjectView.detail(project)


@router.post("/github", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_IMPORT)
async def import_github(
    request: Request,
    payload: GitHubImportRequest,
    current_user: CurrentUser,
    service: ProjectServiceDep,
) -> ProjectResponse:
    project = await service.import_github(
        owner_id=current_user.id, repo_url=payload.repo_url, branch=payload.branch
    )
    return ProjectView.detail(project)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    current_user: CurrentUser, service: ProjectServiceDep
) -> ProjectListResponse:
    items, total = await service.list_projects(current_user.id)
    return ProjectView.collection(items, total)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str, current_user: CurrentUser, service: ProjectServiceDep
) -> ProjectResponse:
    project = await service.get_project(
        project_id=project_id, owner_id=current_user.id
    )
    return ProjectView.detail(project)


@router.post("/{project_id}/detect", response_model=ProjectResponse)
async def detect_stack(
    project_id: str, current_user: CurrentUser, service: ProjectServiceDep
) -> ProjectResponse:
    """Re-run language + framework detection (Phase 2) on an extracted project."""
    project = await service.detect_stack(
        project_id=project_id, owner_id=current_user.id
    )
    return ProjectView.detail(project)


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(
    project_id: str, current_user: CurrentUser, service: ProjectServiceDep
) -> MessageResponse:
    await service.delete_project(project_id=project_id, owner_id=current_user.id)
    return ProjectView.message("Project deleted.")
