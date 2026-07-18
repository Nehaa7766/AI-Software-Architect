"""Unit tests for the project folder-tree builder."""
from pathlib import Path

from app.modules.projects.services.tree_service import TreeService


def _write(root: Path, rel: str, content: str = "x") -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _child(node, name):
    return next(c for c in node.children if c.name == name)


def test_builds_nested_tree(tmp_path: Path):
    _write(tmp_path, "src/app/main.py", "print(1)")
    _write(tmp_path, "src/util.ts", "export const x = 1")
    _write(tmp_path, "README.md", "# docs")

    tree = TreeService().build(tmp_path)

    assert tree.root.type == "dir"
    names = {c.name for c in tree.root.children}
    assert {"src", "README.md"} <= names

    src = _child(tree.root, "src")
    assert src.type == "dir"
    assert {c.name for c in src.children} == {"app", "util.ts"}
    assert tree.total_files == 3  # main.py, util.ts, README.md


def test_non_source_files_are_included(tmp_path: Path):
    # Unlike the scanner, the tree shows EVERYTHING in the archive.
    _write(tmp_path, "logo.png", "binary")
    _write(tmp_path, "data.csv", "a,b")
    tree = TreeService().build(tmp_path)
    names = {c.name for c in tree.root.children}
    assert {"logo.png", "data.csv"} <= names


def test_ignored_dirs_pruned(tmp_path: Path):
    _write(tmp_path, "node_modules/dep/index.js", "x")
    _write(tmp_path, "app.py", "1")
    tree = TreeService().build(tmp_path)
    names = {c.name for c in tree.root.children}
    assert "node_modules" not in names
    assert "app.py" in names


def test_dirs_before_files_and_language_tagged(tmp_path: Path):
    _write(tmp_path, "zeta.py", "1")
    _write(tmp_path, "alpha/inner.py", "1")
    tree = TreeService().build(tmp_path)
    # Directory ("alpha") sorts before file ("zeta.py").
    assert [c.name for c in tree.root.children] == ["alpha", "zeta.py"]
    zeta = _child(tree.root, "zeta.py")
    assert zeta.language == "Python"
    assert zeta.size_bytes is not None
