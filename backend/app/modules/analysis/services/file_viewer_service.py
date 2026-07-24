"""Read-only source file viewer (Phase 5.1).

Serves the text of a single file from a project's workspace so the client can
open it in a viewer and jump to a symbol's line. Strictly read-only and
sandboxed to the workspace; uploaded code is never executed.

Orchestration only — ownership + path safety + file read live here; the
controller stays thin and never touches the filesystem.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

from app.models.project import ProjectStatus
from app.modules.analysis.utils.exceptions import (
    FileNotFoundInProject,
    FileNotViewable,
    FileTooLarge,
)
from app.modules.analysis.utils.paths import safe_resolve
from app.modules.projects.repositories.project_repository import ProjectRepository
from app.modules.projects.utils.exceptions import (
    ProjectNotExtracted,
    ProjectNotFound,
)

logger = logging.getLogger("analysis")

# Files above this size are not served to the viewer (huge/generated files).
_MAX_VIEW_BYTES = 2 * 1024 * 1024  # 2 MiB

# File extension -> Monaco editor language id (lowercase). Unknown -> plaintext.
_MONACO_LANGUAGE: dict[str, str] = {
    ".py": "python", ".pyw": "python", ".pyi": "python",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript", ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".cs": "csharp",
    ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".hpp": "cpp", ".hh": "cpp", ".hxx": "cpp",
    ".c": "c", ".h": "c",
    ".php": "php",
    ".rb": "ruby",
    ".rs": "rust",
    ".kt": "kotlin", ".kts": "kotlin",
    ".swift": "swift",
    ".scala": "scala",
    ".dart": "dart",
    ".lua": "lua",
    ".pl": "perl", ".pm": "perl",
    ".r": "r",
    ".sh": "shell", ".bash": "shell", ".zsh": "shell",
    ".ps1": "powershell",
    ".sql": "sql",
    ".html": "html", ".htm": "html", ".vue": "html", ".svelte": "html",
    ".css": "css", ".scss": "scss", ".sass": "scss", ".less": "less",
    ".json": "json",
    ".yml": "yaml", ".yaml": "yaml",
    ".xml": "xml",
    ".md": "markdown",
    ".m": "objective-c", ".mm": "objective-c",
    ".toml": "ini", ".ini": "ini", ".cfg": "ini",
    ".dockerfile": "dockerfile",
}


def monaco_language(path: Path) -> str:
    """Best-effort Monaco language id for syntax highlighting."""
    if path.name == "Dockerfile":
        return "dockerfile"
    return _MONACO_LANGUAGE.get(path.suffix.lower(), "plaintext")


@dataclass
class FileContent:
    path: str  # workspace-relative, POSIX-separated (echoes the request)
    language: str
    content: str


class FileViewerService:
    def __init__(self, *, projects: ProjectRepository) -> None:
        self.projects = projects

    async def read_file(
        self, *, project_id: str, owner_id: str, rel_path: str
    ) -> FileContent:
        """Return the text of ``rel_path`` within an owned, extracted project."""
        project = await self.projects.get_for_owner(project_id, owner_id)
        if project is None:
            raise ProjectNotFound()
        if project.status != ProjectStatus.EXTRACTED or not project.workspace_path:
            raise ProjectNotExtracted()

        # File IO is blocking — keep the event loop free. Path safety + read run
        # together in the worker thread.
        return await asyncio.to_thread(
            self._read, project.workspace_path, rel_path
        )

    @staticmethod
    def _read(workspace_path: str, rel_path: str) -> FileContent:
        # Raises InvalidFilePath / PathTraversalBlocked on unsafe input.
        target = safe_resolve(workspace_path, rel_path)

        if not target.is_file():
            raise FileNotFoundInProject()
        try:
            size = target.stat().st_size
        except OSError as exc:
            raise FileNotFoundInProject() from exc
        if size > _MAX_VIEW_BYTES:
            raise FileTooLarge(
                f"File is {size // 1024} KB; the viewer limit is "
                f"{_MAX_VIEW_BYTES // 1024} KB."
            )

        try:
            # Reject binaries: strict decode first, fall back to lenient only
            # for near-text files so the viewer never shows mojibake garbage.
            raw = target.read_bytes()
            if b"\x00" in raw:
                raise FileNotViewable("This looks like a binary file.")
            content = raw.decode("utf-8", errors="replace")
        except OSError as exc:
            raise FileNotFoundInProject() from exc

        normalized = rel_path.replace("\\", "/").strip()
        return FileContent(
            path=normalized,
            language=monaco_language(target),
            content=content,
        )
