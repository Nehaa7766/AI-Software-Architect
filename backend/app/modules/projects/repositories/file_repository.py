"""Persistence for ProjectFile rows. The only layer that touches project_files."""
from collections.abc import Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import ProjectFile


class FileRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def replace_for_project(
        self, project_id: str, files: Sequence[dict]
    ) -> int:
        """Atomically swap the file inventory for a project (used by (re)scan).

        Deletes the project's existing rows then bulk-inserts the new set.
        Returns the number of rows inserted.
        """
        await self.db.execute(
            delete(ProjectFile).where(ProjectFile.project_id == project_id)
        )
        rows = [
            ProjectFile(
                project_id=project_id,
                path=f["path"],
                language=f["language"],
                size_bytes=f["size_bytes"],
                content_hash=f["content_hash"],
            )
            for f in files
        ]
        self.db.add_all(rows)
        await self.db.flush()
        return len(rows)

    async def list_for_project(
        self,
        project_id: str,
        *,
        language: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ProjectFile]:
        stmt = select(ProjectFile).where(ProjectFile.project_id == project_id)
        if language:
            stmt = stmt.where(ProjectFile.language == language)
        stmt = stmt.order_by(ProjectFile.path).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def all_for_project(self, project_id: str) -> list[ProjectFile]:
        """Return every file row for a project (unpaged), ordered by path.

        Used by Phase 4 parsing, which must iterate the whole inventory.
        """
        stmt = (
            select(ProjectFile)
            .where(ProjectFile.project_id == project_id)
            .order_by(ProjectFile.path)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_for_project(
        self, project_id: str, *, language: str | None = None
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(ProjectFile)
            .where(ProjectFile.project_id == project_id)
        )
        if language:
            stmt = stmt.where(ProjectFile.language == language)
        result = await self.db.execute(stmt)
        return int(result.scalar_one())

    async def language_breakdown(self, project_id: str) -> dict[str, int]:
        stmt = (
            select(ProjectFile.language, func.count())
            .where(ProjectFile.project_id == project_id)
            .group_by(ProjectFile.language)
            .order_by(func.count().desc())
        )
        result = await self.db.execute(stmt)
        return {language: count for language, count in result.all()}
