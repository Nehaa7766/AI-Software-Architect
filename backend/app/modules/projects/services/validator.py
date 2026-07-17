"""Validation for incoming projects — ZIP archives and GitHub URLs.

Pure validation only: no extraction, no DB writes. Raises domain
``ProjectError`` subclasses that the central handler maps to HTTP responses.
"""
import zipfile
from pathlib import Path

from app.core.config import settings
from app.modules.projects.utils.exceptions import (
    FileTooLarge,
    InvalidArchive,
    UnsupportedFileType,
)


class ProjectValidator:
    def validate_zip_upload(self, *, filename: str | None, size: int) -> None:
        """Cheap pre-checks before the bytes touch disk."""
        if not filename or not filename.lower().endswith(".zip"):
            raise UnsupportedFileType("Only .zip archives are accepted.")
        if size <= 0:
            raise InvalidArchive("Uploaded file is empty.")
        if size > settings.MAX_PROJECT_BYTES:
            raise FileTooLarge(
                f"Archive exceeds the {settings.MAX_PROJECT_BYTES // (1024 * 1024)} MB limit."
            )

    def validate_zip_file(self, zip_path: Path) -> None:
        """Verify on-disk archive integrity (structure + CRC)."""
        try:
            with zipfile.ZipFile(zip_path) as zf:
                bad = zf.testzip()
                if bad is not None:
                    raise InvalidArchive(f"Corrupted entry in archive: {bad}")
                if not zf.namelist():
                    raise InvalidArchive("Archive is empty.")
        except zipfile.BadZipFile as exc:
            raise InvalidArchive("File is not a valid ZIP archive.") from exc
