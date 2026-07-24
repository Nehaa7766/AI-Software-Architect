"""Unit tests for Phase 5 symbol search ranking + query construction."""
from sqlalchemy.dialects import postgresql

from app.models.symbol import SymbolType
from app.modules.analysis.repositories.symbol_repository import build_symbol_search
from app.modules.analysis.services.ranking import (
    RANK_EXACT,
    RANK_NONE,
    RANK_PARENT,
    RANK_PREFIX,
    RANK_SUBSTRING,
    kind_priority,
    sort_key,
    symbol_rank,
)


def test_rank_tiers():
    assert symbol_rank("User", None, "user") == RANK_EXACT
    assert symbol_rank("UserService", None, "user") == RANK_PREFIX
    assert symbol_rank("getUser", None, "user") == RANK_SUBSTRING
    assert symbol_rank("helper", "UserController", "user") == RANK_PARENT
    assert symbol_rank("totally", "unrelated", "user") == RANK_NONE


def test_rank_is_case_insensitive():
    assert symbol_rank("USER", None, "user") == RANK_EXACT
    assert symbol_rank("user", None, "USER") == RANK_EXACT


def test_empty_query_matches_nothing():
    assert symbol_rank("User", None, "   ") == RANK_NONE


def test_kind_priority_orders_definitions_first():
    assert kind_priority(SymbolType.CLASS) < kind_priority(SymbolType.FUNCTION)
    assert kind_priority(SymbolType.FUNCTION) < kind_priority(SymbolType.VARIABLE)
    assert kind_priority(SymbolType.VARIABLE) < kind_priority(SymbolType.IMPORT)
    assert kind_priority(SymbolType.IMPORT) < kind_priority(SymbolType.COMMENT)


def test_sort_key_full_ordering():
    rows = [
        ("getUser", None, SymbolType.FUNCTION),
        ("User", None, SymbolType.CLASS),
        ("user_id", None, SymbolType.VARIABLE),
        ("UserService", None, SymbolType.CLASS),
        ("helper", "UserController", SymbolType.FUNCTION),
    ]
    ordered = sorted(rows, key=lambda r: sort_key(r[0], r[1], r[2], "user"))
    assert [r[0] for r in ordered] == [
        "User",  # exact
        "UserService",  # prefix, class
        "user_id",  # prefix, variable
        "getUser",  # substring
        "helper",  # parent-only match
    ]


def test_shorter_names_win_within_same_tier():
    rows = [
        ("authenticateUser", None, SymbolType.FUNCTION),
        ("auth", None, SymbolType.FUNCTION),
        ("authHandler", None, SymbolType.FUNCTION),
    ]
    ordered = sorted(rows, key=lambda r: sort_key(r[0], r[1], r[2], "auth"))
    # All prefix matches, same kind → shortest name first.
    assert [r[0] for r in ordered] == ["auth", "authHandler", "authenticateUser"]


def test_build_search_compiles_for_postgres():
    select_stmt, count_stmt = build_symbol_search(
        "proj-1", "Handler", symbol_type=SymbolType.FUNCTION, limit=25, offset=50
    )
    sql = str(select_stmt.compile(dialect=postgresql.dialect())).upper()
    assert "ILIKE" in sql
    assert "ORDER BY" in sql
    assert "LIMIT" in sql
    # count query is a scalar count over the same predicate
    csql = str(count_stmt.compile(dialect=postgresql.dialect())).upper()
    assert "COUNT" in csql


def test_build_search_handles_wildcard_query():
    # Must not raise — LIKE wildcards in the query are escaped literally.
    select_stmt, _ = build_symbol_search("proj-1", "50%_off")
    assert str(select_stmt.compile(dialect=postgresql.dialect()))
