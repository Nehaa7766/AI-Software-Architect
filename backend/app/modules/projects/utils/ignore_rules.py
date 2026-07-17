"""Directory ignore rules + an ignore-aware file walker.

Shared by detection (Phase 2) and later scanning phases so every traversal skips
the same vendored / generated / VCS directories.
"""
import os
from collections.abc import Iterator
from pathlib import Path

# Directories that never contain first-party source worth analyzing.
IGNORED_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        "bower_components",
        "dist",
        "build",
        "out",
        ".next",
        ".nuxt",
        ".svelte-kit",
        "venv",
        ".venv",
        "env",
        ".env",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "target",
        "bin",
        "obj",
        "coverage",
        ".cache",
        ".gradle",
        ".idea",
        ".vscode",
        "vendor",
        "Pods",
        ".dart_tool",
    }
)


def is_ignored_dir(name: str) -> bool:
    return name in IGNORED_DIRS


def walk_files(root: Path) -> Iterator[Path]:
    """Yield every file under ``root``, pruning ignored directories in place."""
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune ignored dirs so os.walk never descends into them.
        dirnames[:] = [d for d in dirnames if not is_ignored_dir(d)]
        base = Path(dirpath)
        for name in filenames:
            yield base / name
