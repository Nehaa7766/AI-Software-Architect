"""ZIP safety helpers — defend against Zip-Slip, zip bombs, and unsafe members.

The extractor calls :func:`safe_extract` instead of ``ZipFile.extractall`` so a
malicious archive can never write outside the destination directory or exhaust
disk via a decompression bomb.
"""
import os
import re
import zipfile
from pathlib import Path

from app.core.config import settings
from app.modules.projects.utils.exceptions import (
    ExtractionFailed,
    InvalidArchive,
    UnsafeArchive,
)

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_project_name(raw: str) -> str:
    """Turn an arbitrary filename / repo name into a safe, readable label."""
    stem = Path(raw).name
    # Drop a trailing .zip if present.
    if stem.lower().endswith(".zip"):
        stem = stem[:-4]
    cleaned = _SAFE_NAME.sub("-", stem).strip("-._")
    return cleaned or "project"


def _is_within(base: Path, target: Path) -> bool:
    """True if ``target`` resolves to a path inside ``base``."""
    try:
        target.relative_to(base)
        return True
    except ValueError:
        return False


def assert_safe_archive(zf: zipfile.ZipFile) -> None:
    """Validate archive members before extracting anything.

    Raises on path traversal, absolute paths, symlinks, too many entries, or a
    total uncompressed size that would exceed the configured cap (zip bomb).
    """
    infos = zf.infolist()
    if len(infos) > settings.MAX_PROJECT_FILES:
        raise UnsafeArchive(
            f"Archive has too many entries (> {settings.MAX_PROJECT_FILES})."
        )

    total = 0
    for info in infos:
        name = info.filename
        # Reject absolute paths and traversal sequences outright.
        if name.startswith(("/", "\\")) or os.path.isabs(name):
            raise UnsafeArchive(f"Absolute path in archive: {name!r}")
        if ".." in Path(name).parts:
            raise UnsafeArchive(f"Path traversal in archive: {name!r}")
        # Reject symlinks (mode bits high 16 carry the unix file type).
        mode = info.external_attr >> 16
        if mode and (mode & 0o170000) == 0o120000:
            raise UnsafeArchive(f"Symlink in archive: {name!r}")
        total += info.file_size
        if total > settings.MAX_PROJECT_UNCOMPRESSED_BYTES:
            raise UnsafeArchive("Archive uncompressed size exceeds the limit.")


def safe_extract(zip_path: Path, dest_dir: Path) -> None:
    """Safely extract ``zip_path`` into ``dest_dir``.

    Every member is validated and re-checked against the resolved destination
    so nothing escapes the workspace. Never executes archive contents.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    base = dest_dir.resolve()
    try:
        with zipfile.ZipFile(zip_path) as zf:
            if zf.testzip() is not None:
                raise InvalidArchive("Archive is corrupted.")
            assert_safe_archive(zf)
            for info in zf.infolist():
                if info.is_dir():
                    (base / info.filename).mkdir(parents=True, exist_ok=True)
                    continue
                target = (base / info.filename).resolve()
                if not _is_within(base, target):
                    raise UnsafeArchive(f"Member escapes workspace: {info.filename!r}")
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, open(target, "wb") as out:
                    out.write(src.read())
    except zipfile.BadZipFile as exc:
        raise InvalidArchive("File is not a valid ZIP archive.") from exc
    except UnsafeArchive:
        raise
    except OSError as exc:
        raise ExtractionFailed(f"Could not extract archive: {exc}") from exc
