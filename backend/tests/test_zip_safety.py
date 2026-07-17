"""Unit tests for ZIP safety + project name sanitization (Phase 1)."""
import io
import zipfile
from pathlib import Path

import pytest

from app.modules.projects.utils.exceptions import InvalidArchive, UnsafeArchive
from app.modules.projects.utils.zip_safety import (
    safe_extract,
    sanitize_project_name,
)


def _make_zip(path: Path, members: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)


def test_sanitize_strips_extension_and_unsafe_chars():
    assert sanitize_project_name("Hospital Mgmt!.zip") == "Hospital-Mgmt"
    assert sanitize_project_name("../../etc/passwd") == "passwd"
    assert sanitize_project_name("") == "project"


def test_safe_extract_happy_path(tmp_path: Path):
    zip_path = tmp_path / "p.zip"
    _make_zip(zip_path, {"src/main.py": b"print(1)", "README.md": b"# hi"})
    dest = tmp_path / "out"
    safe_extract(zip_path, dest)
    assert (dest / "src" / "main.py").read_bytes() == b"print(1)"
    assert (dest / "README.md").exists()


def test_safe_extract_rejects_zip_slip(tmp_path: Path):
    zip_path = tmp_path / "evil.zip"
    # Craft a member with a traversal path that escapes the destination.
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("../../escape.txt", b"pwned")
    dest = tmp_path / "out"
    with pytest.raises(UnsafeArchive):
        safe_extract(zip_path, dest)
    assert not (tmp_path / "escape.txt").exists()


def test_safe_extract_rejects_absolute_path(tmp_path: Path):
    zip_path = tmp_path / "abs.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("/abs.txt", b"x")
    with pytest.raises(UnsafeArchive):
        safe_extract(zip_path, tmp_path / "out")


def test_safe_extract_rejects_corrupted_archive(tmp_path: Path):
    bad = tmp_path / "bad.zip"
    bad.write_bytes(b"not a real zip file")
    with pytest.raises(InvalidArchive):
        safe_extract(bad, tmp_path / "out")


def test_safe_extract_rejects_too_many_files(tmp_path: Path, monkeypatch):
    from app.core import config

    monkeypatch.setattr(config.settings, "MAX_PROJECT_FILES", 2)
    zip_path = tmp_path / "many.zip"
    _make_zip(zip_path, {f"f{i}.txt": b"x" for i in range(5)})
    with pytest.raises(UnsafeArchive):
        safe_extract(zip_path, tmp_path / "out")
