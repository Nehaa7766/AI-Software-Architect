"""Parser registry — selects the correct language parser (plugin lookup).

Holds the set of available parsers and resolves a language label to a concrete
:class:`BaseParser`. Registering a new language means appending one parser here
(or via :meth:`register`) — no other code changes (open/closed principle).
"""
from __future__ import annotations

import logging
from collections.abc import Iterable

from app.modules.analysis.services.parsing.base import BaseParser
from app.modules.analysis.services.parsing.javascript_parser import JavaScriptParser
from app.modules.analysis.services.parsing.python_parser import PythonParser
from app.modules.analysis.utils.exceptions import UnsupportedLanguage

logger = logging.getLogger("analysis")


def _default_parsers() -> list[BaseParser]:
    return [PythonParser(), JavaScriptParser()]


class ParserRegistry:
    def __init__(self, parsers: Iterable[BaseParser] | None = None) -> None:
        self._parsers: list[BaseParser] = list(
            parsers if parsers is not None else _default_parsers()
        )

    def register(self, parser: BaseParser) -> None:
        """Add a parser (future languages: Java, Go, C#, PHP, …)."""
        self._parsers.append(parser)

    def supports(self, language: str) -> bool:
        return any(p.supports(language) for p in self._parsers)

    def get_parser(self, language: str) -> BaseParser:
        """Return the parser for ``language`` or raise ``UnsupportedLanguage``."""
        for parser in self._parsers:
            if parser.supports(language):
                return parser
        raise UnsupportedLanguage(language)

    def supported_languages(self) -> set[str]:
        langs: set[str] = set()
        for parser in self._parsers:
            langs |= set(parser.languages)
        return langs
