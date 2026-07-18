"""Unit tests for the Phase 4 Python AST parser."""
from pathlib import Path

from app.models.symbol import SymbolType, Visibility
from app.modules.analysis.services.parsing.python_parser import PythonParser


def _write(root: Path, rel: str, content: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def _by_type(symbols, t):
    return [s for s in symbols if s.symbol_type == t]


SAMPLE = '''\
"""Module docstring."""
import os
from typing import List as L

CONSTANT = 42
threshold = 3

@decorator
class Widget(Base):
    """A widget."""

    kind = "gadget"

    def __init__(self, name):
        self.name = name

    async def _hidden(self) -> None:
        pass


def top_level(a, b=1) -> int:
    # a comment
    return a + b
'''


def test_extracts_all_core_symbols(tmp_path: Path):
    path = _write(tmp_path, "sample.py", SAMPLE)
    symbols = PythonParser().parse(path, "Python")

    classes = _by_type(symbols, SymbolType.CLASS)
    assert [c.name for c in classes] == ["Widget"]
    assert classes[0].docstring == "A widget."
    assert "Base" in classes[0].metadata["bases"]

    functions = {f.name for f in _by_type(symbols, SymbolType.FUNCTION)}
    assert "top_level" in functions

    methods = {m.name: m for m in _by_type(symbols, SymbolType.METHOD)}
    assert set(methods) == {"__init__", "_hidden"}
    assert methods["__init__"].parent_symbol == "Widget"
    assert methods["_hidden"].metadata["is_async"] is True
    assert methods["_hidden"].visibility == Visibility.PROTECTED

    imports = {i.name for i in _by_type(symbols, SymbolType.IMPORT)}
    assert imports == {"os", "L"}

    constants = {c.name for c in _by_type(symbols, SymbolType.CONSTANT)}
    assert "CONSTANT" in constants
    variables = {v.name for v in _by_type(symbols, SymbolType.VARIABLE)}
    assert "threshold" in variables

    decorators = {d.name for d in _by_type(symbols, SymbolType.DECORATOR)}
    assert "decorator" in decorators


def test_module_docstring_captured(tmp_path: Path):
    path = _write(tmp_path, "m.py", SAMPLE)
    symbols = PythonParser().parse(path, "Python")
    docstrings = _by_type(symbols, SymbolType.DOCSTRING)
    assert any(d.name == "<module>" for d in docstrings)


def test_comments_captured(tmp_path: Path):
    path = _write(tmp_path, "c.py", SAMPLE)
    symbols = PythonParser().parse(path, "Python")
    comments = [c.name for c in _by_type(symbols, SymbolType.COMMENT)]
    assert "a comment" in comments


def test_function_signature_reconstructed(tmp_path: Path):
    path = _write(tmp_path, "s.py", SAMPLE)
    symbols = PythonParser().parse(path, "Python")
    fn = _by_type(symbols, SymbolType.FUNCTION)[0]
    assert fn.signature.startswith("def top_level(")
    assert "-> int" in fn.signature


def test_supports_language():
    parser = PythonParser()
    assert parser.supports("Python")
    assert not parser.supports("JavaScript")
