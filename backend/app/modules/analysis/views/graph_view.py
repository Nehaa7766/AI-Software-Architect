"""View layer (presenter) for the dependency graph — maps edges to DTOs."""
from app.models.graph import GraphEdge
from app.modules.analysis.dto.responses import (
    CallGraphSummaryResponse,
    CallNeighborsResponse,
    DependencyGraphResponse,
    DependencySummaryResponse,
    EntryPointResponse,
    EntryPointsResponse,
    GraphEdgeResponse,
    GraphNodeResponse,
    NeighborsResponse,
)
from app.modules.analysis.services.callgraph_service import CallStats, EntryPoint
from app.modules.analysis.services.dependency_service import DependencyStats


class GraphView:
    @staticmethod
    def _edge(e: GraphEdge) -> GraphEdgeResponse:
        return GraphEdgeResponse(
            edge_type=e.edge_type.value,
            source_kind=e.source_kind.value,
            source_id=e.source_id,
            source_name=e.source_name,
            target_kind=e.target_kind.value,
            target_id=e.target_id,
            target_name=e.target_name,
            external=e.external,
        )

    @staticmethod
    def summary(project_id: str, stats: DependencyStats) -> DependencySummaryResponse:
        return DependencySummaryResponse(
            project_id=project_id,
            status="built",
            edges_total=stats.edges_total,
            internal=stats.internal,
            external=stats.external,
            by_type=stats.by_type,
        )

    @staticmethod
    def graph(
        project_id: str,
        edges: list[GraphEdge],
        total: int,
        by_type: dict[str, int],
    ) -> DependencyGraphResponse:
        # Derive the unique node set from the returned edges (for visualization).
        nodes: dict[str, GraphNodeResponse] = {}
        for e in edges:
            for name, kind, node_id, external in (
                (e.source_name, e.source_kind.value, e.source_id, False),
                (e.target_name, e.target_kind.value, e.target_id, e.external),
            ):
                existing = nodes.get(name)
                if existing is None:
                    nodes[name] = GraphNodeResponse(
                        id=node_id, name=name, kind=kind, external=external
                    )
                elif node_id and not existing.id:
                    existing.id = node_id
        return DependencyGraphResponse(
            project_id=project_id,
            nodes=list(nodes.values()),
            edges=[GraphView._edge(e) for e in edges],
            total=total,
            by_type=by_type,
        )

    @staticmethod
    def neighbors(
        node: str, dependents: list[GraphEdge], dependencies: list[GraphEdge]
    ) -> NeighborsResponse:
        return NeighborsResponse(
            node=node,
            dependents=[GraphView._edge(e) for e in dependents],
            dependencies=[GraphView._edge(e) for e in dependencies],
        )

    # ---- Phase 7: call graph ----
    @staticmethod
    def call_summary(project_id: str, stats: CallStats) -> CallGraphSummaryResponse:
        return CallGraphSummaryResponse(
            project_id=project_id,
            status="built",
            calls_total=stats.calls_total,
            internal=stats.internal,
            external=stats.external,
            recursive=stats.recursive,
            files_analyzed=stats.files_analyzed,
        )

    @staticmethod
    def call_neighbors(
        symbol: str, callers: list[GraphEdge], callees: list[GraphEdge]
    ) -> CallNeighborsResponse:
        return CallNeighborsResponse(
            symbol=symbol,
            callers=[GraphView._edge(e) for e in callers],
            callees=[GraphView._edge(e) for e in callees],
        )

    @staticmethod
    def entry_points(
        project_id: str, entry: list[EntryPoint], total: int
    ) -> EntryPointsResponse:
        return EntryPointsResponse(
            project_id=project_id,
            entry_points=[
                EntryPointResponse(
                    name=e.name, file_path=e.file_path, line=e.line
                )
                for e in entry
            ],
            total=total,
        )
