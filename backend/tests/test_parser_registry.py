"""Unit tests for the Phase 4 parser registry (plugin selection)."""
import pytest

from app.modules.analysis.services.parsing.base import BaseParser, ParsedSymbol
from app.modules.analysis.services.parsing.javascript_parser import JavaScriptParser
from app.modules.analysis.services.parsing.python_parser import PythonParser
from app.modules.analysis.services.parsing.registry import ParserRegistry
from app.modules.analysis.utils.exceptions import UnsupportedLanguage


def test_selects_python_parser():
    assert isinstance(ParserRegistry().get_parser("Python"), PythonParser)


def test_javascript_and_typescript_share_parser():
    reg = ParserRegistry()
    assert isinstance(reg.get_parser("JavaScript"), JavaScriptParser)
    assert isinstance(reg.get_parser("TypeScript"), JavaScriptParser)


def test_unsupported_language_raises():
    with pytest.raises(UnsupportedLanguage) as exc:
        ParserRegistry().get_parser("COBOL")
    assert exc.value.language == "COBOL"
    assert exc.value.status_code == 422


def test_supported_languages_reported():
    langs = ParserRegistry().supported_languages()
    assert {"Python", "JavaScript", "TypeScript"} <= langs


def test_register_new_parser_is_extensible():
    class GoParser(BaseParser):
        languages = frozenset({"Go"})

        def parse(self, file_path, language):  # pragma: no cover - trivial
            return [ParsedSymbol(name="x", symbol_type=None, language=language)]

    reg = ParserRegistry(parsers=[])
    assert not reg.supports("Go")
    reg.register(GoParser())
    assert isinstance(reg.get_parser("Go"), GoParser)
