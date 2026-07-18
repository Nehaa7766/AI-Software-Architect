"""Build a nested folder/file tree of an extracted project (for the UI).

Walks the workspace directory (ignore-aware, same pruning as detection/scanning)
and produces a nested structure the client can render as a file explorer. Pure
logic: returns plain dicts; reading disk only, never executing project code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.modules.projects.services.detection.language_detector import LanguageDetector
from app.modules.projects.utils.ignore_rules import is_ignored_dir

# Guard: cap total nodes so a pathological archive can't produce a huge payload.
_MAX_NODES = 5000


@dataclass
class TreeNode:
    name: str
    path: str  # relative, POSIX-separated ("" for the root)
    type: str  # "dir" | "file"
    size_bytes: int | None = None
    language: str | None = None
    children: list["TreeNode"] | None = None


@dataclass
class ProjectTree:
    root: TreeNode
    total_files: int
    total_dirs: int
    truncated: bool = False


class TreeService:
    def __init__(self, languages: LanguageDetector | None = None) -> None:
        self.languages = languages or LanguageDetector()

    def build(self, project_root: Path | str) -> ProjectTree:
        root = Path(project_root)
        counter = {"nodes": 0, "files": 0, "dirs": 0, "truncated": False}
        root_node = TreeNode(name=root.name or "root", path="", type="dir", children=[])
        self._populate(root, root, root_node, counter)
        return ProjectTree(
            root=root_node,
            total_files=counter["files"],
            total_dirs=counter["dirs"],
            truncated=counter["truncated"],
        )

    def _populate(
        self, base: Path, current: Path, node: TreeNode, counter: dict
    ) -> None:
        try:
            entries = sorted(
                current.iterdir(),
                # Directories first, then files; each alphabetical (case-insensitive).
                key=lambda p: (p.is_file(), p.name.lower()),
            )
        except OSError:
            return

        for entry in entries:
            if counter["nodes"] >= _MAX_NODES:
                counter["truncated"] = True
                return
            if entry.is_dir():
                if is_ignored_dir(entry.name):
                    continue
                child = TreeNode(
                    name=entry.name,
                    path=entry.relative_to(base).as_posix(),
                    type="dir",
                    children=[],
                )
                counter["nodes"] += 1
                counter["dirs"] += 1
                node.children.append(child)  # type: ignore[union-attr]
                self._populate(base, entry, child, counter)
            elif entry.is_file():
                try:
                    size = entry.stat().st_size
                except OSError:
                    size = None
                child = TreeNode(
                    name=entry.name,
                    path=entry.relative_to(base).as_posix(),
                    type="file",
                    size_bytes=size,
                    language=self.languages.classify(entry),
                )
                counter["nodes"] += 1
                counter["files"] += 1
                node.children.append(child)  # type: ignore[union-attr]
