"""Workspace + temp-file management for imported projects.

Owns the on-disk layout. Uploaded archives live in a temp dir, projects are
extracted into ``WORKSPACE_DIR/project_<id>/``, and everything is removable so a
failed import leaves nothing behind.
"""
import shutil
import uuid
from pathlib import Path

from app.core.config import settings


class WorkspaceManager:
    def __init__(self) -> None:
        self.root = Path(settings.WORKSPACE_DIR)
        self.tmp_root = Path(settings.PROJECT_TMP_DIR)

    def _ensure_dirs(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.tmp_root.mkdir(parents=True, exist_ok=True)

    def new_tmp_file(self, suffix: str = ".zip") -> Path:
        """Return a unique path in the temp dir for an incoming archive."""
        self._ensure_dirs()
        return self.tmp_root / f"upload_{uuid.uuid4().hex}{suffix}"

    def project_dir(self, project_id: str) -> Path:
        """Deterministic, isolated extraction directory for a project."""
        self._ensure_dirs()
        # Short, filesystem-friendly slug; full id stays in the DB.
        return self.root / f"project_{project_id.replace('-', '')[:12]}"

    @staticmethod
    def resolve_project_root(extract_dir: Path) -> Path:
        """Collapse a single wrapping folder (e.g. GitHub ``repo-main/``).

        If extraction produced exactly one top-level directory and no files,
        treat that directory as the project root; otherwise the extract dir is
        the root.
        """
        entries = [p for p in extract_dir.iterdir()]
        if len(entries) == 1 and entries[0].is_dir():
            return entries[0]
        return extract_dir

    @staticmethod
    def remove(path: Path | str | None) -> None:
        """Best-effort recursive delete; never raises."""
        if not path:
            return
        shutil.rmtree(Path(path), ignore_errors=True)

    @staticmethod
    def remove_file(path: Path | str | None) -> None:
        """Best-effort single-file delete; never raises."""
        if not path:
            return
        try:
            Path(path).unlink(missing_ok=True)
        except OSError:
            pass
