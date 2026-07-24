"""Persistence for GraphEdge rows. The only layer that touches graph_edges."""
from collections.abc import Sequence

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.graph import EdgeType, GraphEdge


class GraphEdgeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def replace_for_project(
        self,
        project_id: str,
        edges: Sequence[dict],
        *,
        edge_types: Sequence[EdgeType] | None = None,
    ) -> int:
        """Atomically swap a project's edges. Returns the number inserted.

        When ``edge_types`` is given, only edges of those types are deleted first
        — so rebuilding the call graph (Phase 7) doesn't wipe the import/inherit
        edges (Phase 6), and vice-versa.
        """
        stmt = delete(GraphEdge).where(GraphEdge.project_id == project_id)
        if edge_types is not None:
            stmt = stmt.where(GraphEdge.edge_type.in_(list(edge_types)))
        await self.db.execute(stmt)
        rows = [
            GraphEdge(
                project_id=project_id,
                edge_type=e["edge_type"],
                source_kind=e["source_kind"],
                source_id=e.get("source_id"),
                source_name=e["source_name"],
                target_kind=e["target_kind"],
                target_id=e.get("target_id"),
                target_name=e["target_name"],
                external=e.get("external", False),
                meta=e.get("metadata"),
            )
            for e in edges
        ]
        self.db.add_all(rows)
        await self.db.flush()
        return len(rows)

    async def list_for_project(
        self,
        project_id: str,
        *,
        edge_type: EdgeType | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> list[GraphEdge]:
        stmt = select(GraphEdge).where(GraphEdge.project_id == project_id)
        if edge_type is not None:
            stmt = stmt.where(GraphEdge.edge_type == edge_type)
        stmt = (
            stmt.order_by(GraphEdge.edge_type, GraphEdge.source_name)
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_for_project(
        self, project_id: str, *, edge_type: EdgeType | None = None
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(GraphEdge)
            .where(GraphEdge.project_id == project_id)
        )
        if edge_type is not None:
            stmt = stmt.where(GraphEdge.edge_type == edge_type)
        result = await self.db.execute(stmt)
        return int(result.scalar_one())

    async def type_breakdown(self, project_id: str) -> dict[str, int]:
        stmt = (
            select(GraphEdge.edge_type, func.count())
            .where(GraphEdge.project_id == project_id)
            .group_by(GraphEdge.edge_type)
        )
        result = await self.db.execute(stmt)
        return {row[0].value: row[1] for row in result.all()}

    async def external_count(self, project_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(GraphEdge)
            .where(GraphEdge.project_id == project_id, GraphEdge.external.is_(True))
        )
        result = await self.db.execute(stmt)
        return int(result.scalar_one())

    async def dependents(
        self, project_id: str, node: str, *, edge_type: EdgeType | None = None
    ) -> list[GraphEdge]:
        """Edges pointing AT ``node`` — i.e. "what imports/depends on X"."""
        stmt = select(GraphEdge).where(
            GraphEdge.project_id == project_id,
            or_(GraphEdge.target_name == node, GraphEdge.target_id == node),
        )
        if edge_type is not None:
            stmt = stmt.where(GraphEdge.edge_type == edge_type)
        stmt = stmt.order_by(GraphEdge.source_name)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def dependencies(
        self, project_id: str, node: str, *, edge_type: EdgeType | None = None
    ) -> list[GraphEdge]:
        """Edges leaving ``node`` — i.e. "what X imports/depends on"."""
        stmt = select(GraphEdge).where(
            GraphEdge.project_id == project_id,
            or_(GraphEdge.source_name == node, GraphEdge.source_id == node),
        )
        if edge_type is not None:
            stmt = stmt.where(GraphEdge.edge_type == edge_type)
        stmt = stmt.order_by(GraphEdge.target_name)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def internal_target_ids(
        self, project_id: str, edge_type: EdgeType
    ) -> set[str]:
        """Distinct internal (resolved) target ids for an edge type.

        Used to find call-graph entry points: callable symbols that are never
        an internal call target have in-degree 0.
        """
        stmt = (
            select(GraphEdge.target_id)
            .where(
                GraphEdge.project_id == project_id,
                GraphEdge.edge_type == edge_type,
                GraphEdge.external.is_(False),
                GraphEdge.target_id.is_not(None),
            )
            .distinct()
        )
        result = await self.db.execute(stmt)
        return {row[0] for row in result.all() if row[0]}
