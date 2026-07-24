"""Safe workspace path resolution for the read-only file viewer (Phase 5.1).

The single defense against path traversal / zip-slip-style escapes. Pure and
side-effect free (no IO beyond ``resolve``) so it can be unit-tested exhaustively
without a workspace on disk.
"""
from __future__ import annotations

import re
from pathlib import Path

from app.modules.analysis.utils.exceptions import (
    InvalidFilePath,
    PathTraversalBlocked,
)

# A leading Windows drive letter, e.g. "C:\..." or "c:/...".
_DRIVE_RE = re.compile(r"^[A-Za-z]:")


def safe_resolve(workspace_root: Path | str, rel_path: str) -> Path:
    """Resolve ``rel_path`` inside ``workspace_root`` or raise.

    Guarantees the returned path is contained within the (symlink-resolved)
    workspace root. Rejects empty/NUL/absolute/drive-qualified inputs up front;
    ``..`` segments and symlinks are neutralized by resolving and then verifying
    containment — a symlink pointing outside the workspace resolves outside and
    is rejected.
    """
    if rel_path is None or not rel_path.strip():
        raise InvalidFilePath("A file path is required.")
    if "\x00" in rel_path:
        raise InvalidFilePath("The file path contains an invalid character.")

    # Normalize Windows separators so the check is OS-independent, then reject
    # anything that is rooted or drive-qualified (must be workspace-relative).
    normalized = rel_path.replace("\\", "/").strip()
    if normalized.startswith("/") or _DRIVE_RE.match(normalized):
        raise InvalidFilePath("The file path must be relative to the project.")

    candidate = Path(normalized)
    if candidate.is_absolute():
        raise InvalidFilePath("The file path must be relative to the project.")

    root = Path(workspace_root).resolve()
    # resolve() collapses ".." and follows symlinks; containment is the guard.
    target = (root / candidate).resolve()

    if target != root and not target.is_relative_to(root):
        raise PathTraversalBlocked()
    return target
