"""Persistence for Symbol rows. The only layer that touches the symbols table."""
from collections.abc import Sequence

from sqlalchemy import case, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.symbol import Symbol, SymbolType
from app.modules.analysis.services.ranking import (
    KIND_PRIORITY,
    RANK_EXACT,
    RANK_NONE,
    RANK_PARENT,
    RANK_PREFIX,
    RANK_SUBSTRING,
)


def _like_escape(value: str) -> str:
    """Escape LIKE/ILIKE wildcards so a user query is matched literally."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def build_symbol_search(
    project_id: str,
    query: str,
    *,
    symbol_type: SymbolType | None = None,
    language: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """Build the ranked-search statements: ``(select_stmt, count_stmt)``.

    Pure/DB-agnostic so it can be compile-tested without a live database.
    Ordering mirrors ``ranking.sort_key``: match tier → kind prominence →
    shorter names → alphabetical.
    """
    q = query.strip()
    esc = _like_escape(q)
    contains = f"%{esc}%"
    prefix = f"{esc}%"
    name_l = func.lower(Symbol.name)
    parent_l = func.lower(func.coalesce(Symbol.parent_symbol, ""))

    where = [
        Symbol.project_id == project_id,
        or_(
            Symbol.name.ilike(contains, escape="\\"),
            Symbol.parent_symbol.ilike(contains, escape="\\"),
        ),
    ]
    if symbol_type is not None:
        where.append(Symbol.symbol_type == symbol_type)
    if language:
        where.append(Symbol.language == language)

    rank = case(
        (name_l == q.lower(), RANK_EXACT),
        (Symbol.name.ilike(prefix, escape="\\"), RANK_PREFIX),
        (Symbol.name.ilike(contains, escape="\\"), RANK_SUBSTRING),
        (parent_l.ilike(contains, escape="\\"), RANK_PARENT),
        else_=RANK_NONE,
    )
    kind_rank = case(
        {k: v for k, v in KIND_PRIORITY.items()},
        value=Symbol.symbol_type,
        else_=9,
    )

    select_stmt = (
        select(Symbol)
        .where(*where)
        # Eager-load the file so results can show "path:line".
        .options(joinedload(Symbol.file))
        .order_by(rank, kind_rank, func.length(Symbol.name), name_l)
        .limit(limit)
        .offset(offset)
    )
    count_stmt = select(func.count()).select_from(Symbol).where(*where)
    return select_stmt, count_stmt


class SymbolRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def replace_for_project(
        self, project_id: str, symbols: Sequence[dict]
    ) -> int:
        """Atomically swap the symbol set for a project (used by (re)parse).

        Deletes the project's existing symbols then bulk-inserts the new set.
        Returns the number of rows inserted.
        """
        await self.db.execute(
            delete(Symbol).where(Symbol.project_id == project_id)
        )
        rows = [
            Symbol(
                project_id=project_id,
                file_id=s["file_id"],
                name=s["name"],
                symbol_type=s["symbol_type"],
                language=s["language"],
                parent_symbol=s.get("parent_symbol"),
                visibility=s["visibility"],
                signature=s.get("signature"),
                docstring=s.get("docstring"),
                line_number=s.get("line_number", 0),
                meta=s.get("metadata"),
            )
            for s in symbols
        ]
        self.db.add_all(rows)
        await self.db.flush()
        return len(rows)

    async def list_for_project(
        self,
        project_id: str,
        *,
        symbol_type: SymbolType | None = None,
        language: str | None = None,
        file_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Symbol]:
        stmt = (
            select(Symbol)
            .where(Symbol.project_id == project_id)
            .options(joinedload(Symbol.file))
        )
        if symbol_type is not None:
            stmt = stmt.where(Symbol.symbol_type == symbol_type)
        if language:
            stmt = stmt.where(Symbol.language == language)
        if file_id:
            stmt = stmt.where(Symbol.file_id == file_id)
        stmt = (
            stmt.order_by(Symbol.file_id, Symbol.line_number)
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def search_for_project(
        self,
        project_id: str,
        query: str,
        *,
        symbol_type: SymbolType | None = None,
        language: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Symbol], int]:
        """Ranked name search within a project. Returns ``(rows, total)``.

        Matches when the query is a substring of the symbol name or its
        enclosing symbol. Ordering mirrors ``ranking.sort_key``: match tier →
        kind prominence → shorter names → alphabetical. The ILIKE filter is
        accelerated by the pg_trgm GIN index on ``symbols.name``.
        """
        select_stmt, count_stmt = build_symbol_search(
            project_id,
            query,
            symbol_type=symbol_type,
            language=language,
            limit=limit,
            offset=offset,
        )
        rows = list((await self.db.execute(select_stmt)).scalars().all())
        total = int((await self.db.execute(count_stmt)).scalar_one())
        return rows, total

    async def count_for_project(
        self,
        project_id: str,
        *,
        symbol_type: SymbolType | None = None,
        language: str | None = None,
        file_id: str | None = None,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(Symbol)
            .where(Symbol.project_id == project_id)
        )
        if symbol_type is not None:
            stmt = stmt.where(Symbol.symbol_type == symbol_type)
        if language:
            stmt = stmt.where(Symbol.language == language)
        if file_id:
            stmt = stmt.where(Symbol.file_id == file_id)
        result = await self.db.execute(stmt)
        return int(result.scalar_one())

    async def type_breakdown(self, project_id: str) -> dict[str, int]:
        """Count symbols per ``symbol_type`` for a project."""
        stmt = (
            select(Symbol.symbol_type, func.count())
            .where(Symbol.project_id == project_id)
            .group_by(Symbol.symbol_type)
        )
        result = await self.db.execute(stmt)
        return {row[0].value: row[1] for row in result.all()}

    async def all_for_project(
        self, project_id: str, *, symbol_types: list[SymbolType] | None = None
    ) -> list[Symbol]:
        """Return every symbol for a project (optionally only certain kinds).

        Used by Phase 6 dependency-graph building, which needs all imports +
        class definitions at once.
        """
        stmt = select(Symbol).where(Symbol.project_id == project_id)
        if symbol_types:
            stmt = stmt.where(Symbol.symbol_type.in_(symbol_types))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def counts_by_file(
        self, project_id: str
    ) -> list[tuple[str, SymbolType, int]]:
        """Return (file_id, symbol_type, count) rows for a project.

        The service turns these into per-file breakdowns keyed by file path.
        """
        stmt = (
            select(Symbol.file_id, Symbol.symbol_type, func.count())
            .where(Symbol.project_id == project_id)
            .group_by(Symbol.file_id, Symbol.symbol_type)
        )
        result = await self.db.execute(stmt)
        return [(row[0], row[1], row[2]) for row in result.all()]

    async def parsed_file_count(self, project_id: str) -> int:
        """Number of distinct files that produced at least one symbol."""
        stmt = (
            select(func.count(func.distinct(Symbol.file_id)))
            .where(Symbol.project_id == project_id)
        )
        result = await self.db.execute(stmt)
        return int(result.scalar_one())
