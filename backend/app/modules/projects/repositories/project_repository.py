"""Persistence for Project rows. The only layer that touches the projects table."""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import ImportSource, Project, ProjectStatus


class ProjectRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        *,
        owner_id: str,
        project_name: str,
        source_type: ImportSource,
        source_location: str,
        status: ProjectStatus = ProjectStatus.UPLOADED,
    ) -> Project:
        project = Project(
            owner_id=owner_id,
            project_name=project_name,
            source_type=source_type,
            source_location=source_location,
            status=status,
        )
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def update(self, project: Project, **fields) -> Project:
        for key, value in fields.items():
            setattr(project, key, value)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def get_for_owner(self, project_id: str, owner_id: str) -> Project | None:
        result = await self.db.execute(
            select(Project).where(
                Project.id == project_id, Project.owner_id == owner_id
            )
        )
        return result.scalar_one_or_none()

    async def list_for_owner(self, owner_id: str) -> list[Project]:
        result = await self.db.execute(
            select(Project)
            .where(Project.owner_id == owner_id)
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_for_owner(self, owner_id: str) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Project).where(Project.owner_id == owner_id)
        )
        return int(result.scalar_one())

    async def delete(self, project: Project) -> None:
        await self.db.delete(project)
        await self.db.flush()
