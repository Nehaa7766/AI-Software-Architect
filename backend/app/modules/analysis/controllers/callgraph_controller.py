"""HTTP handlers for the call graph (Phase 7)."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.security import CurrentUser
from app.modules.analysis.dependencies import get_callgraph_service
from app.modules.analysis.dto.responses import (
    CallGraphSummaryResponse,
    CallNeighborsResponse,
    DependencyGraphResponse,
    EntryPointsResponse,
)
from app.modules.analysis.services.callgraph_service import CallGraphService
from app.modules.analysis.views.graph_view import GraphView

router = APIRouter(prefix="/projects", tags=["analysis"])

CallGraphServiceDep = Annotated[
    CallGraphService, Depends(get_callgraph_service)
]


@router.post("/{project_id}/callgraph", response_model=CallGraphSummaryResponse)
async def build_callgraph(
    project_id: str, current_user: CurrentUser, service: CallGraphServiceDep
) -> CallGraphSummaryResponse:
    """(Re)build the project's call graph from source + parsed symbols."""
    stats = await service.build_project(
        project_id=project_id, owner_id=current_user.id
    )
    return GraphView.call_summary(project_id, stats)


@router.get("/{project_id}/callgraph", response_model=DependencyGraphResponse)
async def get_callgraph(
    project_id: str,
    current_user: CurrentUser,
    service: CallGraphServiceDep,
    limit: Annotated[int, Query(ge=1, le=2000)] = 500,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DependencyGraphResponse:
    """Return the call graph (nodes + call edges)."""
    edges, total, by_type = await service.get_graph(
        project_id=project_id, owner_id=current_user.id, limit=limit, offset=offset
    )
    return GraphView.graph(project_id, edges, total, by_type)


@router.get(
    "/{project_id}/callgraph/neighbors", response_model=CallNeighborsResponse
)
async def get_call_neighbors(
    project_id: str,
    current_user: CurrentUser,
    service: CallGraphServiceDep,
    symbol: Annotated[str, Query(description="Function/method name")],
    direction: Annotated[str, Query(pattern="^(in|out|both)$")] = "both",
) -> CallNeighborsResponse:
    """Where is ``symbol`` used (callers) and what does it call (callees)."""
    callers, callees = await service.get_neighbors(
        project_id=project_id,
        owner_id=current_user.id,
        symbol=symbol,
        direction=direction,
    )
    return GraphView.call_neighbors(symbol, callers, callees)


@router.get(
    "/{project_id}/callgraph/entrypoints", response_model=EntryPointsResponse
)
async def get_entry_points(
    project_id: str,
    current_user: CurrentUser,
    service: CallGraphServiceDep,
    limit: Annotated[int, Query(ge=1, le=1000)] = 200,
) -> EntryPointsResponse:
    """Functions/methods with no internal caller — call-graph entry points."""
    entry, total = await service.get_entry_points(
        project_id=project_id, owner_id=current_user.id, limit=limit
    )
    return GraphView.entry_points(project_id, entry, total)
