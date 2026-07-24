"""Extract call sites from JavaScript / TypeScript via Tree-sitter.

Mirrors the Phase 4 parser's approach: lazy grammar loading with graceful
degradation (returns ``[]`` when tree-sitter is unavailable). Never executes
source.
"""
from __future__ import annotations

import logging

from app.modules.analysis.services.callgraph.base import CallSite

logger = logging.getLogger("analysis")

_GRAMMAR_BY_LANGUAGE = {"JavaScript": "javascript", "TypeScript": "typescript"}
_FUNC_NODES = {
    "function_declaration",
    "generator_function_declaration",
    "function_expression",
    "arrow_function",
    "method_definition",
}

_parsers: dict[str, object] = {}
_pack_missing = False


def _get_parser(language: str):
    global _pack_missing
    grammar = _GRAMMAR_BY_LANGUAGE.get(language)
    if grammar is None or _pack_missing:
        return None
    if grammar in _parsers:
        return _parsers[grammar]
    try:
        from tree_sitter_language_pack import get_parser
    except ImportError:
        _pack_missing = True
        logger.warning("tree_sitter_language_pack missing; JS/TS calls disabled.")
        return None
    try:
        parser = get_parser(grammar)
    except Exception:  # pragma: no cover - defensive
        logger.warning("Failed to load tree-sitter grammar '%s'.", grammar)
        _parsers[grammar] = None
        return None
    _parsers[grammar] = parser
    return parser


def _text(node, src: bytes) -> str:
    return src[node.start_byte : node.end_byte].decode("utf-8", "replace")


def _func_name(node, src: bytes) -> str | None:
    named = node.child_by_field_name("name")
    if named is not None:
        return _text(named, src)
    # Anonymous function/arrow assigned to a name: const foo = () => {} / {foo() {}}
    parent = node.parent
    if parent is not None:
        if parent.type == "variable_declarator":
            n = parent.child_by_field_name("name")
            return _text(n, src) if n is not None else None
        if parent.type == "pair":
            k = parent.child_by_field_name("key")
            return _text(k, src) if k is not None else None
    return None


def _callee_name(fn_node, src: bytes) -> str | None:
    if fn_node is None:
        return None
    if fn_node.type == "identifier":
        return _text(fn_node, src)
    if fn_node.type == "member_expression":  # a.b.foo() -> foo
        prop = fn_node.child_by_field_name("property")
        return _text(prop, src) if prop is not None else None
    return None


def _walk(node, src, calls, caller, caller_parent, current_class):
    for child in node.named_children:
        t = child.type
        if t in ("class_declaration", "abstract_class_declaration"):
            name_node = child.child_by_field_name("name")
            cls = _text(name_node, src) if name_node is not None else current_class
            _walk(child, src, calls, caller, caller_parent, cls)
        elif t in _FUNC_NODES:
            name = _func_name(child, src) or "<anonymous>"
            parent = current_class if t == "method_definition" else None
            _walk(child, src, calls, name, parent, current_class)
        elif t == "call_expression":
            if caller is not None:
                callee = _callee_name(child.child_by_field_name("function"), src)
                if callee:
                    calls.append(
                        CallSite(
                            caller=caller,
                            caller_parent=caller_parent,
                            callee=callee,
                            line=child.start_point[0] + 1,
                        )
                    )
            # Recurse into arguments (nested calls) keeping the same caller.
            _walk(child, src, calls, caller, caller_parent, current_class)
        else:
            _walk(child, src, calls, caller, caller_parent, current_class)


def extract_js_calls(source: bytes, language: str) -> list[CallSite]:
    parser = _get_parser(language)
    if parser is None:
        return []
    tree = parser.parse(source)
    calls: list[CallSite] = []
    _walk(tree.root_node, source, calls, None, None, None)
    return calls
