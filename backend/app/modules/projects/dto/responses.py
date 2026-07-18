"""Response DTOs for the projects module — pure schemas (the View's data shape).

Mapping from ORM models lives in ``views/project_view.py``; these classes carry
no mapping logic so the "view" layer is the single place that turns models into
response bodies.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.project import ImportSource, ProjectStatus


class LanguageStat(BaseModel):
    language: str
    files: int
    bytes: int
    percentage: float


class DetectedStack(BaseModel):
    """Phase 2 detection result persisted on ``Project.stack``."""

    primary_language: str | None = None
    languages: list[LanguageStat] = []
    frameworks: list[str] = []
    package_managers: list[str] = []
    total_files: int = 0
    total_source_bytes: int = 0


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_name: str
    source_type: ImportSource
    source_location: str
    status: ProjectStatus
    error_message: str | None
    primary_language: str | None = None
    stack: DetectedStack | None = None
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
    total: int


class MessageResponse(BaseModel):
    message: str


# ---- Phase 3: scanner responses ----
class ScannedFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    path: str
    language: str
    size_bytes: int
    content_hash: str


class ScanSummaryResponse(BaseModel):
    """Result of running (or re-running) the scanner on a project."""

    total_files: int
    by_language: dict[str, int]


class FileListResponse(BaseModel):
    files: list[ScannedFileResponse]
    total: int
    by_language: dict[str, int]


# ---- Folder tree (file explorer) ----
class TreeNodeResponse(BaseModel):
    name: str
    path: str
    type: str  # "dir" | "file"
    size_bytes: int | None = None
    language: str | None = None
    children: list["TreeNodeResponse"] | None = None


class ProjectTreeResponse(BaseModel):
    root: TreeNodeResponse
    total_files: int
    total_dirs: int
    truncated: bool = False
