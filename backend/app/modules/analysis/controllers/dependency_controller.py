"""HTTP handlers for the dependency graph (Phase 6)."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.security import CurrentUser
from app.models.graph import EdgeType
from app.modules.analysis.dependencies import get_dependency_service
from app.modules.analysis.dto.responses import (
    DependencyGraphResponse,
    DependencySummaryResponse,
    NeighborsResponse,
)
from app.modules.analysis.services.dependency_service import DependencyService
from app.modules.analysis.views.graph_view import GraphView

router = APIRouter(prefix="/projects", tags=["analysis"])

DependencyServiceDep = Annotated[
    DependencyService, Depends(get_dependency_service)
]


@router.post("/{project_id}/dependencies", response_model=DependencySummaryResponse)
async def build_dependencies(
    project_id: str, current_user: CurrentUser, service: DependencyServiceDep
) -> DependencySummaryResponse:
    """(Re)build the project's dependency graph from parsed symbols."""
    stats = await service.build_project(
        project_id=project_id, owner_id=current_user.id
    )
    return GraphView.summary(project_id, stats)


@router.get("/{project_id}/dependencies", response_model=DependencyGraphResponse)
async def get_dependencies(
    project_id: str,
    current_user: CurrentUser,
    service: DependencyServiceDep,
    edge_type: Annotated[EdgeType | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=2000)] = 500,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DependencyGraphResponse:
    """Return the dependency graph (nodes + edges), optionally filtered by type."""
    edges, total, by_type = await service.get_graph(
        project_id=project_id,
        owner_id=current_user.id,
        edge_type=edge_type,
        limit=limit,
        offset=offset,
    )
    return GraphView.graph(project_id, edges, total, by_type)


@router.get(
    "/{project_id}/dependencies/neighbors", response_model=NeighborsResponse
)
async def get_neighbors(
    project_id: str,
    current_user: CurrentUser,
    service: DependencyServiceDep,
    node: Annotated[str, Query(description="File path or symbol name")],
    direction: Annotated[str, Query(pattern="^(in|out|both)$")] = "both",
    edge_type: Annotated[EdgeType | None, Query()] = None,
) -> NeighborsResponse:
    """Traverse the graph around ``node`` — what imports it / what it imports."""
    dependents, dependencies = await service.get_neighbors(
        project_id=project_id,
        owner_id=current_user.id,
        node=node,
        direction=direction,
        edge_type=edge_type,
    )
    return GraphView.neighbors(node, dependents, dependencies)
