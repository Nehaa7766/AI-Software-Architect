"""Top-level orchestration for project import (Phase 1).

Coordinates importers (get a validated archive on disk), the extractor (safe
extract into the workspace), and the repository (persist the lifecycle). HTTP
concerns stay in the controller; on-disk concerns stay in the services.
"""
import asyncio
import logging

from fastapi import UploadFile

from app.models.project import ImportSource, Project, ProjectFile, ProjectStatus
from app.modules.projects.repositories.file_repository import FileRepository
from app.modules.projects.repositories.project_repository import ProjectRepository
from app.modules.projects.services.detection import DetectionService
from app.modules.projects.services.extractor import Extractor
from app.modules.projects.services.github_importer import GitHubImporter
from app.modules.projects.services.scanner_service import ScannerService, ScanResult
from app.modules.projects.services.staging import StagedArchive
from app.modules.projects.services.workspace_manager import WorkspaceManager
from app.modules.projects.services.zip_importer import ZipImporter
from app.modules.projects.utils.exceptions import (
    ProjectError,
    ProjectNotExtracted,
    ProjectNotFound,
)

logger = logging.getLogger("projects")


class ProjectService:
    def __init__(
        self,
        *,
        projects: ProjectRepository,
        zip_importer: ZipImporter,
        github_importer: GitHubImporter,
        extractor: Extractor,
        workspace: WorkspaceManager,
        detection: DetectionService,
        files: FileRepository,
        scanner: ScannerService,
    ) -> None:
        self.projects = projects
        self.zip_importer = zip_importer
        self.github_importer = github_importer
        self.extractor = extractor
        self.workspace = workspace
        self.detection = detection
        self.files = files
        self.scanner = scanner

    # ---- Imports ----
    async def import_zip(self, *, owner_id: str, upload: UploadFile) -> Project:
        staged = await self.zip_importer.stage(upload)
        return await self._extract_and_persist(owner_id=owner_id, staged=staged)

    async def import_github(
        self, *, owner_id: str, repo_url: str, branch: str | None
    ) -> Project:
        staged = await self.github_importer.stage(repo_url=repo_url, branch=branch)
        return await self._extract_and_persist(owner_id=owner_id, staged=staged)

    async def _extract_and_persist(
        self, *, owner_id: str, staged: StagedArchive
    ) -> Project:
        # Record the project as UPLOADED before extraction so a crash mid-way
        # still leaves an auditable row.
        project = await self.projects.create(
            owner_id=owner_id,
            project_name=staged.project_name,
            source_type=staged.source_type,
            source_location=staged.source_location,
            status=ProjectStatus.UPLOADED,
        )
        try:
            # Extraction is CPU/IO-bound and synchronous — keep the loop free.
            root = await asyncio.to_thread(
                self.extractor.extract, staged.tmp_path, project.id
            )
            project = await self.projects.update(
                project,
                workspace_path=str(root),
                status=ProjectStatus.EXTRACTED,
                error_message=None,
            )
            # Phase 2: detect the stack. Non-fatal — a detection failure must not
            # fail the import; the project stays EXTRACTED with an empty stack.
            await self._run_detection(project, root)
            # Phase 3: inventory the source files. Also best-effort.
            await self._run_scan(project, root)
            return project
        except ProjectError as exc:
            await self.projects.update(
                project, status=ProjectStatus.FAILED, error_message=exc.message
            )
            self.workspace.remove(self.workspace.project_dir(project.id))
            raise
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected import failure for project %s", project.id)
            await self.projects.update(
                project, status=ProjectStatus.FAILED, error_message="Import failed."
            )
            self.workspace.remove(self.workspace.project_dir(project.id))
            raise ProjectError("Import failed.") from exc
        finally:
            # The staged archive is no longer needed once extracted (or failed).
            self.workspace.remove_file(staged.tmp_path)

    # ---- Detection (Phase 2) ----
    async def _run_detection(self, project: Project, root) -> None:
        """Detect and persist the stack; swallow failures (best-effort)."""
        try:
            stack = await asyncio.to_thread(self.detection.detect, root)
            await self.projects.update(
                project,
                primary_language=stack.get("primary_language"),
                stack=stack,
            )
        except Exception:  # pragma: no cover - defensive, detection is best-effort
            logger.exception("Stack detection failed for project %s", project.id)

    async def detect_stack(self, *, project_id: str, owner_id: str) -> Project:
        """Re-run detection on an already-extracted project."""
        project = await self.get_project(project_id=project_id, owner_id=owner_id)
        if project.status != ProjectStatus.EXTRACTED or not project.workspace_path:
            raise ProjectNotExtracted()
        stack = await asyncio.to_thread(self.detection.detect, project.workspace_path)
        return await self.projects.update(
            project,
            primary_language=stack.get("primary_language"),
            stack=stack,
        )

    # ---- Scanning (Phase 3) ----
    async def _run_scan(self, project: Project, root) -> None:
        """Scan + persist the file inventory; swallow failures (best-effort)."""
        try:
            result = await asyncio.to_thread(self.scanner.scan, root)
            await self._persist_scan(project.id, result)
        except Exception:  # pragma: no cover - defensive, scanning is best-effort
            logger.exception("File scan failed for project %s", project.id)

    async def _persist_scan(self, project_id: str, result: ScanResult) -> None:
        await self.files.replace_for_project(
            project_id,
            [
                {
                    "path": f.path,
                    "language": f.language,
                    "size_bytes": f.size_bytes,
                    "content_hash": f.content_hash,
                }
                for f in result.files
            ],
        )

    async def scan_project(
        self, *, project_id: str, owner_id: str
    ) -> tuple[int, dict[str, int]]:
        """Re-scan an extracted project; returns (total_files, by_language)."""
        project = await self.get_project(project_id=project_id, owner_id=owner_id)
        if project.status != ProjectStatus.EXTRACTED or not project.workspace_path:
            raise ProjectNotExtracted()
        result = await asyncio.to_thread(self.scanner.scan, project.workspace_path)
        await self._persist_scan(project.id, result)
        return result.total_files, result.by_language

    async def list_files(
        self,
        *,
        project_id: str,
        owner_id: str,
        language: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ProjectFile], int, dict[str, int]]:
        """List a project's scanned files (owner-scoped) with paging + breakdown."""
        # Ownership check — raises if the project isn't the caller's.
        await self.get_project(project_id=project_id, owner_id=owner_id)
        items = await self.files.list_for_project(
            project_id, language=language, limit=limit, offset=offset
        )
        total = await self.files.count_for_project(project_id, language=language)
        breakdown = await self.files.language_breakdown(project_id)
        return items, total, breakdown

    # ---- Reads ----
    async def list_projects(self, owner_id: str) -> tuple[list[Project], int]:
        items = await self.projects.list_for_owner(owner_id)
        return items, len(items)

    async def get_project(self, *, project_id: str, owner_id: str) -> Project:
        project = await self.projects.get_for_owner(project_id, owner_id)
        if project is None:
            raise ProjectNotFound()
        return project

    # ---- Delete ----
    async def delete_project(self, *, project_id: str, owner_id: str) -> None:
        project = await self.get_project(project_id=project_id, owner_id=owner_id)
        # Remove workspace files first, then the DB row.
        self.workspace.remove(project.workspace_path)
        self.workspace.remove(self.workspace.project_dir(project.id))
        await self.projects.delete(project)
