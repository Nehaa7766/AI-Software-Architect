"""Phase 7 — build and query the call graph.

Extracts call sites from source (Phase 4 symbols only hold definitions), resolves
each caller and callee to a function/method symbol, and stores directed
``CALL`` edges in the shared ``graph_edges`` table. Cross-file calls and recursion
are handled; entry points are functions with no internal callers.

Edge resolution (``build_call_edges``) is pure and unit-tested; the service adds
ownership, file reading, persistence, and traversal.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Iterable

from app.models.graph import EdgeType, GraphEdge, NodeKind
from app.models.project import ProjectStatus
from app.models.symbol import SymbolType
from app.modules.analysis.repositories.graph_repository import GraphEdgeRepository
from app.modules.analysis.repositories.symbol_repository import SymbolRepository
from app.modules.analysis.services.callgraph import CallSite, extract_calls
from app.modules.projects.repositories.file_repository import FileRepository
from app.modules.projects.repositories.project_repository import ProjectRepository
from app.modules.projects.utils.exceptions import (
    ProjectNotExtracted,
    ProjectNotFound,
)

logger = logging.getLogger("analysis")

_CALLABLE_TYPES = (
    SymbolType.FUNCTION,
    SymbolType.METHOD,
    SymbolType.ARROW_FUNCTION,
)
_MAX_PARSE_BYTES = 2 * 1024 * 1024


@dataclass
class CallStats:
    calls_total: int = 0
    internal: int = 0
    external: int = 0
    recursive: int = 0
    files_analyzed: int = 0


@dataclass
class EntryPoint:
    name: str
    file_path: str | None
    line: int


def _resolve_caller(
    file_callables: list[SimpleNamespace], caller: str, caller_parent: str | None
) -> SimpleNamespace | None:
    """Pick the symbol a call site belongs to, preferring a class match."""
    candidates = [s for s in file_callables if s.name == caller]
    if not candidates:
        return None
    if caller_parent is not None:
        for c in candidates:
            if c.parent_symbol == caller_parent:
                return c
    for c in candidates:
        if c.parent_symbol is None:
            return c
    return candidates[0]


def build_call_edges(
    files: Iterable[SimpleNamespace],
    symbols: Iterable[SimpleNamespace],
    file_calls: dict[str, list[CallSite]],
) -> list[dict]:
    """Resolve extracted call sites to CALL edges (pure).

    ``file_calls`` maps a file id to its call sites. Callees resolve to a
    callable symbol in the same file first, then to a project-wide *unique*
    match; anything else (builtins, library calls, ambiguous names) becomes an
    external edge.
    """
    files = list(files)
    symbols = list(symbols)
    path_by_id = {f.id: f.path for f in files}

    callables = [s for s in symbols if s.symbol_type in _CALLABLE_TYPES]
    by_file: dict[str, list[SimpleNamespace]] = {}
    for s in callables:
        by_file.setdefault(s.file_id, []).append(s)

    # Project-wide name index for cross-file resolution.
    project_by_name: dict[str, list[SimpleNamespace]] = {}
    for s in callables:
        project_by_name.setdefault(s.name, []).append(s)

    edges: list[dict] = []
    seen: set[tuple] = set()

    def add(edge: dict) -> None:
        key = (edge.get("source_id"), edge.get("target_id"), edge["target_name"])
        if key in seen:
            return
        seen.add(key)
        edges.append(edge)

    for file_id, calls in file_calls.items():
        local = by_file.get(file_id, [])
        for c in calls:
            src = _resolve_caller(local, c.caller, c.caller_parent)
            if src is None:
                continue  # can't attribute the call to a known symbol

            # Resolve callee: same file → unique project-wide → external.
            target = None
            same_file = [s for s in local if s.name == c.callee]
            if same_file:
                target = same_file[0]
            else:
                matches = project_by_name.get(c.callee, [])
                if len(matches) == 1:
                    target = matches[0]

            recursive = target is not None and target.id == src.id
            if target is not None:
                add(
                    {
                        "edge_type": EdgeType.CALL,
                        "source_kind": NodeKind.SYMBOL,
                        "source_id": src.id,
                        "source_name": src.name,
                        "target_kind": NodeKind.SYMBOL,
                        "target_id": target.id,
                        "target_name": target.name,
                        "external": False,
                        "metadata": {
                            "file": path_by_id.get(file_id),
                            "line": c.line,
                            "recursive": recursive,
                        },
                    }
                )
            else:
                add(
                    {
                        "edge_type": EdgeType.CALL,
                        "source_kind": NodeKind.SYMBOL,
                        "source_id": src.id,
                        "source_name": src.name,
                        "target_kind": NodeKind.SYMBOL,
                        "target_id": None,
                        "target_name": c.callee,
                        "external": True,
                        "metadata": {"file": path_by_id.get(file_id), "line": c.line},
                    }
                )
    return edges


class CallGraphService:
    def __init__(
        self,
        *,
        edges: GraphEdgeRepository,
        symbols: SymbolRepository,
        files: FileRepository,
        projects: ProjectRepository,
    ) -> None:
        self.edges = edges
        self.symbols = symbols
        self.files = files
        self.projects = projects

    async def build_project(
        self, *, project_id: str, owner_id: str
    ) -> CallStats:
        project = await self._get_extracted_project(project_id, owner_id)
        files = await self.files.all_for_project(project_id)
        symbols = await self.symbols.all_for_project(
            project_id, symbol_types=list(_CALLABLE_TYPES)
        )

        rows, analyzed = await asyncio.to_thread(
            self._extract_all, Path(project.workspace_path), files, symbols
        )
        await self.edges.replace_for_project(
            project_id, rows, edge_types=[EdgeType.CALL]
        )

        external = sum(1 for r in rows if r["external"])
        recursive = sum(1 for r in rows if (r.get("metadata") or {}).get("recursive"))
        stats = CallStats(
            calls_total=len(rows),
            internal=len(rows) - external,
            external=external,
            recursive=recursive,
            files_analyzed=analyzed,
        )
        logger.info(
            "Built call graph for %s: %d calls (%d internal)",
            project_id,
            stats.calls_total,
            stats.internal,
        )
        return stats

    def _extract_all(
        self, root: Path, files: list, symbols: list
    ) -> tuple[list[dict], int]:
        file_calls: dict[str, list[CallSite]] = {}
        analyzed = 0
        for f in files:
            abs_path = root / f.path
            try:
                if not abs_path.is_file() or abs_path.stat().st_size > _MAX_PARSE_BYTES:
                    continue
                source = abs_path.read_bytes()
                calls = extract_calls(source, f.language)
            except SyntaxError:
                continue  # unparseable file — skip, don't abort the build
            except Exception:  # noqa: BLE001 - one bad file must not fail the run
                logger.exception("Call extraction failed for %s", f.path)
                continue
            if calls:
                file_calls[f.id] = calls
            analyzed += 1
        rows = build_call_edges(files, symbols, file_calls)
        return rows, analyzed

    async def get_graph(
        self,
        *,
        project_id: str,
        owner_id: str,
        limit: int = 500,
        offset: int = 0,
    ) -> tuple[list[GraphEdge], int, dict[str, int]]:
        await self._get_owned_project(project_id, owner_id)
        items = await self.edges.list_for_project(
            project_id, edge_type=EdgeType.CALL, limit=limit, offset=offset
        )
        total = await self.edges.count_for_project(
            project_id, edge_type=EdgeType.CALL
        )
        return items, total, {"call": total}

    async def get_neighbors(
        self, *, project_id: str, owner_id: str, symbol: str, direction: str = "both"
    ) -> tuple[list[GraphEdge], list[GraphEdge]]:
        """``(callers, callees)`` for a symbol — "where is fn used / what it calls"."""
        await self._get_owned_project(project_id, owner_id)
        callers: list[GraphEdge] = []
        callees: list[GraphEdge] = []
        if direction in ("in", "both"):
            callers = await self.edges.dependents(
                project_id, symbol, edge_type=EdgeType.CALL
            )
        if direction in ("out", "both"):
            callees = await self.edges.dependencies(
                project_id, symbol, edge_type=EdgeType.CALL
            )
        return callers, callees

    async def get_entry_points(
        self, *, project_id: str, owner_id: str, limit: int = 200
    ) -> tuple[list[EntryPoint], int]:
        """Callable symbols with no internal caller (call-graph roots)."""
        await self._get_owned_project(project_id, owner_id)
        callables = await self.symbols.all_for_project(
            project_id, symbol_types=list(_CALLABLE_TYPES)
        )
        called = await self.edges.internal_target_ids(project_id, EdgeType.CALL)
        files = await self.files.all_for_project(project_id)
        path_by_id = {f.id: f.path for f in files}

        roots = [s for s in callables if s.id not in called]
        roots.sort(key=lambda s: (path_by_id.get(s.file_id, ""), s.line_number))
        entry = [
            EntryPoint(
                name=s.name,
                file_path=path_by_id.get(s.file_id),
                line=s.line_number,
            )
            for s in roots
        ]
        return entry[:limit], len(entry)

    # ---- Project lookups ----
    async def _get_owned_project(self, project_id: str, owner_id: str):
        project = await self.projects.get_for_owner(project_id, owner_id)
        if project is None:
            raise ProjectNotFound()
        return project

    async def _get_extracted_project(self, project_id: str, owner_id: str):
        project = await self._get_owned_project(project_id, owner_id)
        if project.status != ProjectStatus.EXTRACTED or not project.workspace_path:
            raise ProjectNotExtracted()
        return project
