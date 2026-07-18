"""Persistence for Symbol rows. The only layer that touches the symbols table."""
from collections.abc import Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.symbol import Symbol, SymbolType


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
        stmt = select(Symbol).where(Symbol.project_id == project_id)
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
