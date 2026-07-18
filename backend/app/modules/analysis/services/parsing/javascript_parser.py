"""JavaScript / TypeScript parser built on Tree-sitter.

Tree-sitter produces a concrete syntax tree via a compiled grammar; it never
executes the source, so it is safe on untrusted project code. Grammars are
loaded lazily from ``tree_sitter_language_pack`` (prebuilt wheels). If the
dependency is unavailable the parser degrades gracefully — ``parse`` logs and
returns an empty list rather than raising — so the rest of the pipeline (and
the Python parser) keeps working.

Extracted: classes, functions, arrow functions, methods, interfaces, enums,
type aliases, variables, constants, imports, exports, and decorators.
"""
from __future__ import annotations

import logging
from pathlib import Path

from app.models.symbol import SymbolType, Visibility
from app.modules.analysis.services.parsing.base import BaseParser, ParsedSymbol

logger = logging.getLogger("analysis")

# Language label (from the Phase 2 detector) -> tree-sitter grammar name.
_GRAMMAR_BY_LANGUAGE = {
    "JavaScript": "javascript",
    "TypeScript": "typescript",
}
_SIGNATURE_MAX = 2000


class JavaScriptParser(BaseParser):
    languages = frozenset({"JavaScript", "TypeScript"})

    def __init__(self) -> None:
        # Cache one parser per grammar; loaded on first use.
        self._parsers: dict[str, object] = {}
        self._pack_available: bool | None = None

    def parse(self, file_path: Path, language: str) -> list[ParsedSymbol]:
        parser = self._get_parser(language)
        if parser is None:
            return []
        source = Path(file_path).read_bytes()
        tree = parser.parse(source)
        symbols: list[ParsedSymbol] = []
        self._walk(tree.root_node, source, parent=None, symbols=symbols, language=language)
        return symbols

    # ---- Grammar loading (lazy, cached, degrades gracefully) ----
    def _get_parser(self, language: str):
        grammar = _GRAMMAR_BY_LANGUAGE.get(language)
        if grammar is None:
            return None
        if grammar in self._parsers:
            return self._parsers[grammar]
        try:
            from tree_sitter_language_pack import get_parser  # lazy import
        except ImportError:
            if self._pack_available is not False:
                logger.warning(
                    "tree_sitter_language_pack is not installed; "
                    "JavaScript/TypeScript parsing is disabled."
                )
            self._pack_available = False
            return None
        try:
            parser = get_parser(grammar)
        except Exception:  # pragma: no cover - defensive (missing grammar build)
            logger.warning("Failed to load tree-sitter grammar '%s'.", grammar)
            self._parsers[grammar] = None
            return None
        self._parsers[grammar] = parser
        return parser

    # ---- Tree traversal ----
    def _walk(
        self,
        node,
        source: bytes,
        *,
        parent: str | None,
        symbols: list[ParsedSymbol],
        language: str,
    ) -> None:
        for child in node.named_children:
            handler = self._DISPATCH.get(child.type)
            if handler is not None:
                handler(self, child, source, parent, symbols, language)
            else:
                # Descend through wrappers (export statements, blocks, …).
                self._walk(
                    child, source, parent=parent, symbols=symbols, language=language
                )

    def _handle_class(self, node, source, parent, symbols, language):
        name = self._child_name(node, source)
        if name:
            symbols.append(
                ParsedSymbol(
                    name=name,
                    symbol_type=SymbolType.CLASS,
                    language=language,
                    line_number=self._line(node),
                    parent_symbol=parent,
                    visibility=self._visibility(name),
                    signature=self._truncate(f"class {name}"),
                    metadata={"decorators": self._decorators(node, source)},
                )
            )
        body = node.child_by_field_name("body")
        if body is not None:
            self._walk(body, source, parent=name or parent, symbols=symbols, language=language)

    def _handle_function(self, node, source, parent, symbols, language):
        name = self._child_name(node, source) or "<anonymous>"
        symbols.append(
            ParsedSymbol(
                name=name,
                symbol_type=SymbolType.FUNCTION,
                language=language,
                line_number=self._line(node),
                parent_symbol=parent,
                visibility=self._visibility(name),
                signature=self._signature(node, source),
                metadata={"is_async": self._is_async(node, source)},
            )
        )

    def _handle_method(self, node, source, parent, symbols, language):
        name = self._child_name(node, source) or "<anonymous>"
        symbols.append(
            ParsedSymbol(
                name=name,
                symbol_type=SymbolType.METHOD,
                language=language,
                line_number=self._line(node),
                parent_symbol=parent,
                visibility=self._visibility(name),
                signature=self._signature(node, source),
                metadata={
                    "is_async": self._is_async(node, source),
                    "decorators": self._decorators(node, source),
                },
            )
        )

    def _handle_interface(self, node, source, parent, symbols, language):
        name = self._child_name(node, source)
        if name:
            symbols.append(
                ParsedSymbol(
                    name=name,
                    symbol_type=SymbolType.INTERFACE,
                    language=language,
                    line_number=self._line(node),
                    parent_symbol=parent,
                    visibility=self._visibility(name),
                    signature=self._truncate(f"interface {name}"),
                )
            )

    def _handle_enum(self, node, source, parent, symbols, language):
        name = self._child_name(node, source)
        if name:
            symbols.append(
                ParsedSymbol(
                    name=name,
                    symbol_type=SymbolType.ENUM,
                    language=language,
                    line_number=self._line(node),
                    parent_symbol=parent,
                    visibility=self._visibility(name),
                    signature=self._truncate(f"enum {name}"),
                )
            )

    def _handle_type_alias(self, node, source, parent, symbols, language):
        name = self._child_name(node, source)
        if name:
            symbols.append(
                ParsedSymbol(
                    name=name,
                    symbol_type=SymbolType.TYPE_ALIAS,
                    language=language,
                    line_number=self._line(node),
                    parent_symbol=parent,
                    visibility=self._visibility(name),
                )
            )

    def _handle_variable(self, node, source, parent, symbols, language):
        # `const`/`let`/`var` — a lexical/variable declaration may bind several
        # names and may bind an arrow function (which we surface as a function).
        kind_node = node.child(0)
        kind = self._text(kind_node, source) if kind_node is not None else "var"
        for declarator in node.named_children:
            if declarator.type != "variable_declarator":
                continue
            name = self._child_name(declarator, source)
            if not name:
                continue
            value = declarator.child_by_field_name("value")
            if value is not None and value.type in ("arrow_function", "function"):
                symbols.append(
                    ParsedSymbol(
                        name=name,
                        symbol_type=SymbolType.ARROW_FUNCTION
                        if value.type == "arrow_function"
                        else SymbolType.FUNCTION,
                        language=language,
                        line_number=self._line(declarator),
                        parent_symbol=parent,
                        visibility=self._visibility(name),
                        signature=self._signature(value, source, name=name),
                        metadata={"is_async": self._is_async(value, source)},
                    )
                )
            else:
                symbols.append(
                    ParsedSymbol(
                        name=name,
                        symbol_type=SymbolType.CONSTANT
                        if kind == "const"
                        else SymbolType.VARIABLE,
                        language=language,
                        line_number=self._line(declarator),
                        parent_symbol=parent,
                        visibility=self._visibility(name),
                        metadata={"kind": kind},
                    )
                )

    def _handle_import(self, node, source, parent, symbols, language):
        text = self._text(node, source)
        symbols.append(
            ParsedSymbol(
                name=self._import_source(node, source) or text[:200],
                symbol_type=SymbolType.IMPORT,
                language=language,
                line_number=self._line(node),
                signature=self._truncate(text),
                metadata={"source": self._import_source(node, source)},
            )
        )

    def _handle_export(self, node, source, parent, symbols, language):
        symbols.append(
            ParsedSymbol(
                name=self._child_name(node, source) or "<export>",
                symbol_type=SymbolType.EXPORT,
                language=language,
                line_number=self._line(node),
                signature=self._truncate(self._text(node, source).split("{")[0].strip()),
            )
        )
        # An export wraps a declaration — descend so the class/function inside is
        # also captured with its real type.
        self._walk(node, source, parent=parent, symbols=symbols, language=language)

    # ---- Node helpers ----
    def _child_name(self, node, source) -> str | None:
        name_node = node.child_by_field_name("name")
        if name_node is not None:
            return self._text(name_node, source)
        for child in node.named_children:
            if child.type in ("identifier", "type_identifier", "property_identifier"):
                return self._text(child, source)
        return None

    def _decorators(self, node, source) -> list[str]:
        out: list[str] = []
        for child in node.children:
            if child.type == "decorator":
                out.append(self._text(child, source).lstrip("@"))
        return out

    def _import_source(self, node, source) -> str | None:
        src = node.child_by_field_name("source")
        if src is not None:
            return self._text(src, source).strip("'\"")
        return None

    def _is_async(self, node, source) -> bool:
        return "async" in self._text(node, source)[:16]

    def _signature(self, node, source, *, name: str | None = None) -> str:
        params = node.child_by_field_name("parameters")
        params_text = self._text(params, source) if params is not None else "()"
        label = name or self._child_name(node, source) or ""
        return self._truncate(f"function {label}{params_text}".strip())

    @staticmethod
    def _visibility(name: str) -> Visibility:
        # TS/JS: `#field` is a hard-private class member; `_name` is a common
        # convention for protected/internal.
        if name.startswith("#"):
            return Visibility.PRIVATE
        if name.startswith("_"):
            return Visibility.PROTECTED
        return Visibility.PUBLIC

    @staticmethod
    def _line(node) -> int:
        return node.start_point[0] + 1  # tree-sitter rows are 0-based

    @staticmethod
    def _text(node, source: bytes) -> str:
        if node is None:
            return ""
        return source[node.start_byte : node.end_byte].decode("utf-8", "replace")

    @staticmethod
    def _truncate(text: str) -> str:
        text = " ".join(text.split())
        return text if len(text) <= _SIGNATURE_MAX else text[: _SIGNATURE_MAX - 1] + "…"


# Tree-sitter node type -> handler. Defined after the class so methods resolve.
JavaScriptParser._DISPATCH = {
    "class_declaration": JavaScriptParser._handle_class,
    "abstract_class_declaration": JavaScriptParser._handle_class,
    "function_declaration": JavaScriptParser._handle_function,
    "generator_function_declaration": JavaScriptParser._handle_function,
    "method_definition": JavaScriptParser._handle_method,
    "interface_declaration": JavaScriptParser._handle_interface,
    "enum_declaration": JavaScriptParser._handle_enum,
    "type_alias_declaration": JavaScriptParser._handle_type_alias,
    "lexical_declaration": JavaScriptParser._handle_variable,
    "variable_declaration": JavaScriptParser._handle_variable,
    "import_statement": JavaScriptParser._handle_import,
    "export_statement": JavaScriptParser._handle_export,
}
