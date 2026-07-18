"""Parser plugin contract for Phase 4 AST parsing.

Every language parser implements :class:`BaseParser` and returns a list of
:class:`ParsedSymbol` — a normalized, language-independent shape. Because all
parsers share this interface and output, adding a new language is a matter of
writing a new parser and registering it; no existing code changes (OCP + LSP).

Parsers analyze source **statically** and must never execute user code.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from app.models.symbol import SymbolType, Visibility


@dataclass
class ParsedSymbol:
    """A single normalized symbol extracted from a source file.

    Mirrors the ``Symbol`` ORM model but carries no persistence concerns —
    ``project_id``/``file_id`` are attached by the service layer.
    """

    name: str
    symbol_type: SymbolType
    language: str
    line_number: int = 0
    parent_symbol: str | None = None
    visibility: Visibility = Visibility.PUBLIC
    signature: str | None = None
    docstring: str | None = None
    metadata: dict = field(default_factory=dict)

    def dedupe_key(self) -> tuple:
        """Identity used to drop duplicate symbols within a single file."""
        return (
            self.name,
            self.symbol_type,
            self.line_number,
            self.parent_symbol,
        )


class BaseParser(ABC):
    """Common interface every language parser must implement."""

    #: Human-readable language labels this parser handles (as produced by the
    #: Phase 2 language detector, e.g. "Python", "TypeScript").
    languages: frozenset[str] = frozenset()

    def supports(self, language: str) -> bool:
        """Return True if this parser can parse ``language``."""
        return language in self.languages

    @abstractmethod
    def parse(self, file_path: Path, language: str) -> list[ParsedSymbol]:
        """Statically parse ``file_path`` and return its normalized symbols.

        Implementations must be side-effect free and must never execute the
        source. On a malformed file they should raise; the service layer turns
        that into a skip-and-continue so one bad file never aborts a project.
        """
        raise NotImplementedError


def classify_visibility_by_underscore(name: str) -> Visibility:
    """Python-style visibility heuristic (shared by underscore-convention langs).

    ``__dunder__`` and public names are ``PUBLIC``; a single leading underscore
    is ``PROTECTED``; a non-dunder ``__`` prefix (name mangling) is ``PRIVATE``.
    """
    if name.startswith("__") and name.endswith("__"):
        return Visibility.PUBLIC
    if name.startswith("__"):
        return Visibility.PRIVATE
    if name.startswith("_"):
        return Visibility.PROTECTED
    return Visibility.PUBLIC
