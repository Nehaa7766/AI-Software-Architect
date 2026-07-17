"""Shared value object produced by importers and consumed by the project service."""
from dataclasses import dataclass
from pathlib import Path

from app.models.project import ImportSource


@dataclass
class StagedArchive:
    """A validated archive sitting in the temp dir, ready to extract."""

    tmp_path: Path
    project_name: str
    source_type: ImportSource
    source_location: str  # original filename (ZIP) or repo URL (GITHUB)
