"""Archive extraction — thin wrapper around the safe-extract primitive.

Keeps the Zip-Slip / zip-bomb defenses (``zip_safety``) behind a single seam so
both the ZIP and GitHub importers extract identically.
"""
from pathlib import Path

from app.modules.projects.services.workspace_manager import WorkspaceManager
from app.modules.projects.utils.zip_safety import safe_extract


class Extractor:
    def __init__(self, workspace: WorkspaceManager) -> None:
        self.workspace = workspace

    def extract(self, zip_path: Path, project_id: str) -> Path:
        """Extract ``zip_path`` for ``project_id`` and return the project root.

        The destination is unique per project, so re-importing never overwrites
        an existing project's files.
        """
        dest = self.workspace.project_dir(project_id)
        # Guard against a leftover dir from a prior failed attempt.
        self.workspace.remove(dest)
        safe_extract(zip_path, dest)
        return self.workspace.resolve_project_root(dest)
