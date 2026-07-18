"""Python source parser built on the standard-library ``ast`` module.

``ast.parse`` compiles source to an abstract syntax tree **without executing
it**, so this parser is safe against untrusted project code. Comments are not
represented in the AST, so they are recovered separately via ``tokenize`` (also
non-executing).

Extracted: classes, functions, methods, variables, constants, imports,
decorators, docstrings, and comments.
"""
from __future__ import annotations

import ast
import io
import logging
import tokenize
from pathlib import Path

from app.models.symbol import SymbolType, Visibility
from app.modules.analysis.services.parsing.base import (
    BaseParser,
    ParsedSymbol,
    classify_visibility_by_underscore,
)

logger = logging.getLogger("analysis")

# Guard: cap comments captured per file so a generated/minified file cannot
# explode the symbol table.
_MAX_COMMENTS = 500
_SIGNATURE_MAX = 2000


class PythonParser(BaseParser):
    languages = frozenset({"Python"})

    def parse(self, file_path: Path, language: str) -> list[ParsedSymbol]:
        source = Path(file_path).read_text(encoding="utf-8", errors="replace")
        # ast.parse does NOT execute the code; it only builds the syntax tree.
        tree = ast.parse(source)
        symbols: list[ParsedSymbol] = []

        module_doc = ast.get_docstring(tree)
        if module_doc:
            symbols.append(
                ParsedSymbol(
                    name="<module>",
                    symbol_type=SymbolType.DOCSTRING,
                    language=language,
                    line_number=1,
                    docstring=module_doc,
                )
            )

        self._walk_body(tree.body, parent=None, symbols=symbols, language=language)
        symbols.extend(self._extract_comments(source, language))
        return symbols

    # ---- AST traversal ----
    def _walk_body(
        self,
        body: list[ast.stmt],
        *,
        parent: str | None,
        symbols: list[ParsedSymbol],
        language: str,
    ) -> None:
        for node in body:
            if isinstance(node, ast.ClassDef):
                self._handle_class(node, parent, symbols, language)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._handle_function(node, parent, symbols, language)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                self._handle_assignment(node, parent, symbols, language)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                self._handle_import(node, symbols, language)

    def _handle_class(
        self,
        node: ast.ClassDef,
        parent: str | None,
        symbols: list[ParsedSymbol],
        language: str,
    ) -> None:
        bases = [self._expr(b) for b in node.bases]
        decorators = [self._expr(d) for d in node.decorator_list]
        symbols.append(
            ParsedSymbol(
                name=node.name,
                symbol_type=SymbolType.CLASS,
                language=language,
                line_number=node.lineno,
                parent_symbol=parent,
                visibility=classify_visibility_by_underscore(node.name),
                signature=self._truncate(
                    f"class {node.name}({', '.join(bases)})"
                    if bases
                    else f"class {node.name}"
                ),
                docstring=ast.get_docstring(node),
                metadata={"bases": bases, "decorators": decorators},
            )
        )
        self._emit_decorators(node.decorator_list, node.name, symbols, language)
        # Recurse: functions defined directly in a class body are methods.
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._handle_function(
                    child, node.name, symbols, language, is_method=True
                )
            elif isinstance(child, ast.ClassDef):
                self._handle_class(child, node.name, symbols, language)
            elif isinstance(child, (ast.Assign, ast.AnnAssign)):
                self._handle_assignment(
                    child, node.name, symbols, language, is_class_attr=True
                )

    def _handle_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        parent: str | None,
        symbols: list[ParsedSymbol],
        language: str,
        *,
        is_method: bool = False,
    ) -> None:
        decorators = [self._expr(d) for d in node.decorator_list]
        symbols.append(
            ParsedSymbol(
                name=node.name,
                symbol_type=SymbolType.METHOD if is_method else SymbolType.FUNCTION,
                language=language,
                line_number=node.lineno,
                parent_symbol=parent,
                visibility=classify_visibility_by_underscore(node.name),
                signature=self._function_signature(node),
                docstring=ast.get_docstring(node),
                metadata={
                    "decorators": decorators,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "returns": self._expr(node.returns) if node.returns else None,
                },
            )
        )
        self._emit_decorators(node.decorator_list, node.name, symbols, language)
        # Nested functions/classes.
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._handle_function(child, node.name, symbols, language)
            elif isinstance(child, ast.ClassDef):
                self._handle_class(child, node.name, symbols, language)

    def _handle_assignment(
        self,
        node: ast.Assign | ast.AnnAssign,
        parent: str | None,
        symbols: list[ParsedSymbol],
        language: str,
        *,
        is_class_attr: bool = False,
    ) -> None:
        targets = (
            node.targets if isinstance(node, ast.Assign) else [node.target]
        )
        for target in targets:
            for name in self._names_from_target(target):
                # ALL_CAPS at module/class scope is treated as a constant.
                is_const = name.isupper() and len(name) > 1
                symbols.append(
                    ParsedSymbol(
                        name=name,
                        symbol_type=SymbolType.CONSTANT
                        if is_const
                        else SymbolType.VARIABLE,
                        language=language,
                        line_number=node.lineno,
                        parent_symbol=parent,
                        visibility=classify_visibility_by_underscore(name),
                        metadata={"class_attribute": is_class_attr},
                    )
                )

    def _handle_import(
        self,
        node: ast.Import | ast.ImportFrom,
        symbols: list[ParsedSymbol],
        language: str,
    ) -> None:
        if isinstance(node, ast.Import):
            for alias in node.names:
                symbols.append(
                    ParsedSymbol(
                        name=alias.asname or alias.name,
                        symbol_type=SymbolType.IMPORT,
                        language=language,
                        line_number=node.lineno,
                        signature=f"import {alias.name}"
                        + (f" as {alias.asname}" if alias.asname else ""),
                        metadata={"module": alias.name, "alias": alias.asname},
                    )
                )
        else:
            module = node.module or ""
            for alias in node.names:
                symbols.append(
                    ParsedSymbol(
                        name=alias.asname or alias.name,
                        symbol_type=SymbolType.IMPORT,
                        language=language,
                        line_number=node.lineno,
                        signature=f"from {module} import {alias.name}"
                        + (f" as {alias.asname}" if alias.asname else ""),
                        metadata={
                            "module": module,
                            "imported": alias.name,
                            "alias": alias.asname,
                            "level": node.level,
                        },
                    )
                )

    def _emit_decorators(
        self,
        decorator_list: list[ast.expr],
        owner: str,
        symbols: list[ParsedSymbol],
        language: str,
    ) -> None:
        for dec in decorator_list:
            symbols.append(
                ParsedSymbol(
                    name=self._expr(dec),
                    symbol_type=SymbolType.DECORATOR,
                    language=language,
                    line_number=getattr(dec, "lineno", 0),
                    parent_symbol=owner,
                )
            )

    # ---- Comments (tokenize — non-executing) ----
    def _extract_comments(
        self, source: str, language: str
    ) -> list[ParsedSymbol]:
        out: list[ParsedSymbol] = []
        try:
            tokens = tokenize.generate_tokens(io.StringIO(source).readline)
            for tok in tokens:
                if tok.type != tokenize.COMMENT:
                    continue
                text = tok.string.lstrip("#").strip()
                if not text:
                    continue
                out.append(
                    ParsedSymbol(
                        name=text[:200],
                        symbol_type=SymbolType.COMMENT,
                        language=language,
                        line_number=tok.start[0],
                    )
                )
                if len(out) >= _MAX_COMMENTS:
                    break
        except (tokenize.TokenError, IndentationError, SyntaxError):
            # Comment recovery is best-effort; never let it fail the parse.
            logger.debug("Comment tokenization failed; skipping comments.")
        return out

    # ---- Helpers ----
    def _function_signature(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> str:
        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        try:
            args = ast.unparse(node.args)
        except Exception:  # pragma: no cover - defensive across ast versions
            args = ""
        returns = f" -> {self._expr(node.returns)}" if node.returns else ""
        return self._truncate(f"{prefix} {node.name}({args}){returns}")

    @staticmethod
    def _names_from_target(target: ast.expr) -> list[str]:
        if isinstance(target, ast.Name):
            return [target.id]
        if isinstance(target, (ast.Tuple, ast.List)):
            names: list[str] = []
            for elt in target.elts:
                if isinstance(elt, ast.Name):
                    names.append(elt.id)
            return names
        return []

    @staticmethod
    def _expr(node: ast.expr | None) -> str:
        if node is None:
            return ""
        try:
            return ast.unparse(node)
        except Exception:  # pragma: no cover - defensive
            return getattr(node, "id", node.__class__.__name__)

    @staticmethod
    def _truncate(text: str) -> str:
        return text if len(text) <= _SIGNATURE_MAX else text[: _SIGNATURE_MAX - 1] + "…"
