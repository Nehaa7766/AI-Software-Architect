"""Unit tests for the Phase 3 project scanner."""
import hashlib
from pathlib import Path

from app.modules.projects.services.scanner_service import ScannerService


def _write(root: Path, rel: str, content: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_scan_inventories_only_source_files(tmp_path: Path):
    _write(tmp_path, "app/main.py", "print('hi')\n")
    _write(tmp_path, "app/util.ts", "export const x = 1\n")
    _write(tmp_path, "README.md", "# docs")  # not a source language -> excluded
    _write(tmp_path, "data.bin", "\x00\x01")  # not source -> excluded
    _write(tmp_path, "node_modules/dep/index.js", "x")  # ignored dir

    result = ScannerService().scan(tmp_path)

    paths = {f.path for f in result.files}
    assert paths == {"app/main.py", "app/util.ts"}
    assert result.total_files == 2
    assert result.by_language == {"Python": 1, "TypeScript": 1}


def test_scan_records_size_and_sha256(tmp_path: Path):
    _write(tmp_path, "x.py", "print('hello world')\n")
    # Compare against the actual on-disk bytes (newline translation is OS-dependent).
    raw = (tmp_path / "x.py").read_bytes()

    result = ScannerService().scan(tmp_path)
    f = result.files[0]

    assert f.path == "x.py"
    assert f.language == "Python"
    assert f.size_bytes == len(raw)
    assert f.content_hash == hashlib.sha256(raw).hexdigest()


def test_scan_paths_are_posix_relative(tmp_path: Path):
    _write(tmp_path, "src/deeply/nested/file.py", "x=1")
    result = ScannerService().scan(tmp_path)
    assert result.files[0].path == "src/deeply/nested/file.py"  # forward slashes


def test_scan_empty_project(tmp_path: Path):
    _write(tmp_path, "notes.md", "nothing source here")
    result = ScannerService().scan(tmp_path)
    assert result.total_files == 0
    assert result.files == []
    assert result.by_language == {}


def test_scan_results_sorted_by_path(tmp_path: Path):
    _write(tmp_path, "z.py", "1")
    _write(tmp_path, "a.py", "1")
    _write(tmp_path, "m.py", "1")
    result = ScannerService().scan(tmp_path)
    assert [f.path for f in result.files] == ["a.py", "m.py", "z.py"]
