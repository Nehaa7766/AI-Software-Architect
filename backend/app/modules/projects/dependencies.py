"""FastAPI dependency providers for the projects module.

Wires the repository + importer/extractor services per request so controllers
stay thin and the dependency graph is explicit (DIP).
"""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.projects.repositories.file_repository import FileRepository
from app.modules.projects.repositories.project_repository import ProjectRepository
from app.modules.projects.services.detection import DetectionService
from app.modules.projects.services.extractor import Extractor
from app.modules.projects.services.github_importer import GitHubImporter
from app.modules.projects.services.project_service import ProjectService
from app.modules.projects.services.scanner_service import ScannerService
from app.modules.projects.services.validator import ProjectValidator
from app.modules.projects.services.workspace_manager import WorkspaceManager
from app.modules.projects.services.zip_importer import ZipImporter

DbSession = Annotated[AsyncSession, Depends(get_db)]

# These services are stateless — safe to share as module singletons.
_workspace = WorkspaceManager()
_validator = ProjectValidator()
_extractor = Extractor(_workspace)
_zip_importer = ZipImporter(validator=_validator, workspace=_workspace)
_github_importer = GitHubImporter(validator=_validator, workspace=_workspace)
_detection = DetectionService()
_scanner = ScannerService()


def get_project_repository(db: DbSession) -> ProjectRepository:
    return ProjectRepository(db)


def get_file_repository(db: DbSession) -> FileRepository:
    return FileRepository(db)


def get_project_service(
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    files: Annotated[FileRepository, Depends(get_file_repository)],
) -> ProjectService:
    return ProjectService(
        projects=projects,
        zip_importer=_zip_importer,
        github_importer=_github_importer,
        extractor=_extractor,
        workspace=_workspace,
        detection=_detection,
        files=files,
        scanner=_scanner,
    )
