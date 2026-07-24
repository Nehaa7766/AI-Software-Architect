"""Relevance ranking for symbol search (Phase 5 — Symbol Index).

The rules here are the single source of truth for how a symbol matches a query
and how matches are ordered. They are expressed as pure functions (unit-tested)
and mirrored as SQL ``case`` expressions in the repository so ranking + paging
happen DB-side. Keep the two in sync — the tiers below are deliberately simple.
"""
from __future__ import annotations

from app.models.symbol import SymbolType

# Match tiers, best (lowest) first. Used as the primary sort key.
RANK_EXACT = 0  # name equals the query (case-insensitive)
RANK_PREFIX = 1  # name starts with the query
RANK_SUBSTRING = 2  # name contains the query
RANK_PARENT = 3  # only the enclosing symbol's name contains the query
RANK_NONE = 4  # no textual match (should be excluded by the WHERE filter)

# Secondary sort key: how prominent a kind is in search results. Definitions a
# developer usually searches for (classes, functions) outrank incidental symbols
# (imports, comments). Lower sorts first.
KIND_PRIORITY: dict[SymbolType, int] = {
    SymbolType.CLASS: 0,
    SymbolType.INTERFACE: 1,
    SymbolType.STRUCT: 1,
    SymbolType.ENUM: 1,
    SymbolType.FUNCTION: 2,
    SymbolType.METHOD: 2,
    SymbolType.ARROW_FUNCTION: 2,
    SymbolType.TYPE_ALIAS: 3,
    SymbolType.CONSTANT: 3,
    SymbolType.PROPERTY: 4,
    SymbolType.VARIABLE: 4,
    SymbolType.NAMESPACE: 5,
    SymbolType.PACKAGE: 5,
    SymbolType.IMPORT: 6,
    SymbolType.EXPORT: 6,
    SymbolType.DECORATOR: 7,
    SymbolType.COMMENT: 8,
    SymbolType.DOCSTRING: 8,
}

_KIND_PRIORITY_FALLBACK = 9


def kind_priority(symbol_type: SymbolType) -> int:
    """Search prominence of a symbol kind (lower sorts first)."""
    return KIND_PRIORITY.get(symbol_type, _KIND_PRIORITY_FALLBACK)


def symbol_rank(name: str, parent_symbol: str | None, query: str) -> int:
    """Match tier for a symbol against ``query`` (case-insensitive).

    Returns one of the ``RANK_*`` constants; ``RANK_NONE`` when nothing matches.
    """
    q = query.strip().lower()
    if not q:
        return RANK_NONE
    n = (name or "").lower()
    if n == q:
        return RANK_EXACT
    if n.startswith(q):
        return RANK_PREFIX
    if q in n:
        return RANK_SUBSTRING
    if parent_symbol and q in parent_symbol.lower():
        return RANK_PARENT
    return RANK_NONE


def sort_key(
    name: str, parent_symbol: str | None, symbol_type: SymbolType, query: str
) -> tuple[int, int, int, str]:
    """Full ordering key mirroring the DB sort: (rank, kind, len(name), name).

    Exposed for tests and any in-memory ranking; the repository builds the
    equivalent ordering in SQL.
    """
    return (
        symbol_rank(name, parent_symbol, query),
        kind_priority(symbol_type),
        len(name or ""),
        (name or "").lower(),
    )
