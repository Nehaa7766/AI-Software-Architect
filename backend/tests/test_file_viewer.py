"""Unit tests for Phase 5.1 file-viewer path safety + language + reading."""
from pathlib import Path

import pytest

from app.modules.analysis.services.file_viewer_service import (
    FileViewerService,
    monaco_language,
)
from app.modules.analysis.utils.exceptions import (
    FileNotFoundInProject,
    FileNotViewable,
    FileTooLarge,
    InvalidFilePath,
    PathTraversalBlocked,
)
from app.modules.analysis.utils.paths import safe_resolve


def _mk(root: Path, rel: str, content: str = "x") -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ---- safe_resolve ----
def test_resolves_valid_relative_path(tmp_path: Path):
    _mk(tmp_path, "app/main.py")
    target = safe_resolve(tmp_path, "app/main.py")
    assert target == (tmp_path / "app/main.py").resolve()


def test_rejects_parent_traversal(tmp_path: Path):
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (tmp_path / "secret.txt").write_text("top secret")
    with pytest.raises(PathTraversalBlocked):
        safe_resolve(workspace, "../secret.txt")


def test_rejects_deep_traversal(tmp_path: Path):
    with pytest.raises(PathTraversalBlocked):
        safe_resolve(tmp_path, "../../../../../../etc/passwd")


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "   ",
        "/etc/passwd",
        "\\\\server\\share",
        "C:\\Windows\\System32",
        "c:/Windows/System32",
        "app/\x00.py",
    ],
)
def test_rejects_absolute_and_malformed(tmp_path: Path, bad: str):
    with pytest.raises(InvalidFilePath):
        safe_resolve(tmp_path, bad)


def test_backslashes_normalized_within_workspace(tmp_path: Path):
    _mk(tmp_path, "app/util.py")
    target = safe_resolve(tmp_path, "app\\util.py")
    assert target == (tmp_path / "app/util.py").resolve()


def test_symlink_escape_blocked(tmp_path: Path):
    workspace = tmp_path / "ws"
    workspace.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret")
    link = workspace / "link.txt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported in this environment")
    with pytest.raises(PathTraversalBlocked):
        safe_resolve(workspace, "link.txt")


# ---- monaco_language ----
@pytest.mark.parametrize(
    "name,expected",
    [
        ("a.py", "python"),
        ("a.ts", "typescript"),
        ("a.tsx", "typescript"),
        ("a.js", "javascript"),
        ("a.java", "java"),
        ("a.go", "go"),
        ("a.cs", "csharp"),
        ("a.cpp", "cpp"),
        ("a.rb", "ruby"),
        ("Dockerfile", "dockerfile"),
        ("a.unknownext", "plaintext"),
    ],
)
def test_monaco_language(name: str, expected: str):
    assert monaco_language(Path(name)) == expected


# ---- FileViewerService._read ----
def test_read_returns_content_and_language(tmp_path: Path):
    _mk(tmp_path, "app/auth.py", "def login():\n    pass\n")
    result = FileViewerService._read(str(tmp_path), "app/auth.py")
    assert result.path == "app/auth.py"
    assert result.language == "python"
    assert "def login()" in result.content


def test_read_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundInProject):
        FileViewerService._read(str(tmp_path), "nope.py")


def test_read_binary_rejected(tmp_path: Path):
    (tmp_path / "img.py").write_bytes(b"\x89PNG\x00\x01\x02")
    with pytest.raises(FileNotViewable):
        FileViewerService._read(str(tmp_path), "img.py")


def test_read_too_large(tmp_path: Path):
    big = "a" * (2 * 1024 * 1024 + 10)
    (tmp_path / "big.py").write_text(big, encoding="utf-8")
    with pytest.raises(FileTooLarge):
        FileViewerService._read(str(tmp_path), "big.py")


def test_read_traversal_blocked(tmp_path: Path):
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (tmp_path / "secret.txt").write_text("nope")
    with pytest.raises(PathTraversalBlocked):
        FileViewerService._read(str(workspace), "../secret.txt")
