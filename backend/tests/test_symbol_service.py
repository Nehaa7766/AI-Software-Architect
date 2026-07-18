"""Unit tests for the Phase 4 symbol service extraction logic (pure paths)."""
from pathlib import Path
from types import SimpleNamespace

from app.models.symbol import SymbolType, Visibility
from app.modules.analysis.services.parsing.base import ParsedSymbol
from app.modules.analysis.services.symbol_service import SymbolService


def _service() -> SymbolService:
    # Repositories/registry are only exercised by the async DB paths, which we
    # don't touch here; the pure extraction uses the default registry.
    return SymbolService(symbols=None, files=None, projects=None)


def _file(file_id: str, path: str, language: str) -> SimpleNamespace:
    return SimpleNamespace(id=file_id, path=path, language=language)


def _write(root: Path, rel: str, content: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_extract_all_collects_rows_and_stats(tmp_path: Path):
    _write(tmp_path, "a.py", "def f():\n    return 1\n")
    _write(tmp_path, "b.py", "class C:\n    pass\n")
    files = [_file("f1", "a.py", "Python"), _file("f2", "b.py", "Python")]

    result = _service()._extract_all(tmp_path, files)

    assert result.files_parsed == 2
    assert result.files_failed == 0
    assert any(r["name"] == "f" and r["symbol_type"] == SymbolType.FUNCTION for r in result.rows)
    assert all(r["file_id"] in {"f1", "f2"} for r in result.rows)


def test_unparsable_file_is_skipped_not_fatal(tmp_path: Path):
    _write(tmp_path, "good.py", "x = 1\n")
    _write(tmp_path, "bad.py", "def (:\n")  # syntax error
    files = [_file("g", "good.py", "Python"), _file("b", "bad.py", "Python")]

    result = _service()._extract_all(tmp_path, files)

    assert result.files_parsed == 1
    assert result.files_failed == 1
    assert any(r["name"] == "x" for r in result.rows)


def test_unsupported_language_file_is_skipped(tmp_path: Path):
    _write(tmp_path, "main.go", "package main\n")
    files = [_file("g", "main.go", "Go")]

    result = _service()._extract_all(tmp_path, files)

    assert result.files_parsed == 0
    assert result.files_skipped == 1
    assert result.rows == []


def test_missing_file_on_disk_is_skipped(tmp_path: Path):
    files = [_file("x", "does_not_exist.py", "Python")]
    result = _service()._extract_all(tmp_path, files)
    assert result.files_skipped == 1
    assert result.files_parsed == 0


def test_validate_and_dedupe():
    svc = SymbolService
    dupes = [
        ParsedSymbol(name="a", symbol_type=SymbolType.VARIABLE, language="Python", line_number=1),
        ParsedSymbol(name="a", symbol_type=SymbolType.VARIABLE, language="Python", line_number=1),
        ParsedSymbol(name="", symbol_type=SymbolType.VARIABLE, language="Python", line_number=2),
        ParsedSymbol(name="b", symbol_type=SymbolType.VARIABLE, language="Python", line_number=3),
    ]
    out = svc._validate_and_dedupe(dupes)
    assert [s.name for s in out] == ["a", "b"]  # dupe collapsed, empty dropped


def test_to_row_truncates_and_maps_metadata():
    sym = ParsedSymbol(
        name="x" * 600,
        symbol_type=SymbolType.CLASS,
        language="Python",
        line_number=5,
        visibility=Visibility.PRIVATE,
        metadata={"bases": ["A"]},
    )
    row = SymbolService._to_row("fid", sym)
    assert len(row["name"]) == 512
    assert row["file_id"] == "fid"
    assert row["metadata"] == {"bases": ["A"]}
    assert row["visibility"] == Visibility.PRIVATE
