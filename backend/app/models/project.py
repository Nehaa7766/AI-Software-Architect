"""SQLAlchemy ORM model for imported projects (Phase 1 — import only).

A ``Project`` row records *where a project came from* and *where it lives on
disk*. No parsed source code, symbols, or analysis is stored in this phase.
"""
import enum
import uuid

from sqlalchemy import JSON, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


def _uuid() -> str:
    return str(uuid.uuid4())


class ImportSource(str, enum.Enum):
    """How the project entered the system."""

    ZIP = "ZIP"
    GITHUB = "GITHUB"


class ProjectStatus(str, enum.Enum):
    """Lifecycle of an imported project during Phase 1."""

    UPLOADED = "UPLOADED"  # archive received + validated, not yet extracted
    EXTRACTED = "EXTRACTED"  # ready in the workspace
    FAILED = "FAILED"  # import or extraction failed


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[ImportSource] = mapped_column(
        SAEnum(ImportSource, name="import_source"), nullable=False
    )
    # Original filename (ZIP) or repository URL (GITHUB).
    source_location: Mapped[str] = mapped_column(String(1024), nullable=False)
    # Absolute/relative path to the extracted project root in the workspace.
    workspace_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus, name="project_status"),
        default=ProjectStatus.UPLOADED,
        nullable=False,
    )
    # Populated on FAILED so the client can show why.
    error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # ---- Phase 2: detected technology stack ----
    # Highest-count source language; convenient for listing/sorting.
    primary_language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Full detection result: languages (with counts), frameworks, package managers.
    # Stored as JSON so the schema can grow without a migration per field.
    stack: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    owner: Mapped["User"] = relationship(back_populates="projects")  # noqa: F821
    files: Mapped[list["ProjectFile"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class ProjectFile(Base, TimestampMixin):
    """Phase 3 — one row per in-scope source file discovered by the scanner.

    Holds metadata only (path, language, size, content hash); file *contents*
    are not stored in the database, only on disk in the workspace.
    """

    __tablename__ = "project_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Path relative to the project workspace root, POSIX-separated.
    path: Mapped[str] = mapped_column(String(1024), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    # SHA-256 hex digest of the file contents (enables Phase 18 incremental scans).
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    project: Mapped["Project"] = relationship(back_populates="files")
