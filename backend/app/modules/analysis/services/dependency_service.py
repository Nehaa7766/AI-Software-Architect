"""Phase 6 — build and query the project dependency graph.

Derives directed edges from the already-parsed symbols (no re-reading of source):
- **import**  file -> file (internal) or file -> module (external)
- **inherits** class -> base class (internal symbol) or -> external base

Edge building is pure (``build_edges``) and unit-tested; the service adds
ownership, persistence, and traversal ("what imports X").
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Iterable

from app.models.graph import EdgeType, GraphEdge, NodeKind
from app.models.project import ProjectStatus
from app.models.symbol import SymbolType
from app.modules.analysis.repositories.graph_repository import GraphEdgeRepository
from app.modules.analysis.repositories.symbol_repository import SymbolRepository
from app.modules.analysis.services.import_resolver import (
    resolve_js_import,
    resolve_python_import,
)
from app.modules.projects.repositories.file_repository import FileRepository
from app.modules.projects.repositories.project_repository import ProjectRepository
from app.modules.projects.utils.exceptions import (
    ProjectNotExtracted,
    ProjectNotFound,
)

logger = logging.getLogger("analysis")


@dataclass
class DependencyStats:
    edges_total: int = 0
    internal: int = 0
    external: int = 0
    by_type: dict[str, int] = field(default_factory=dict)


def _base_simple_name(base: str) -> str | None:
    """Reduce a base-class expression to a bare class name.

    ``app.models.Base`` -> ``Base``; ``Generic[T]`` -> ``Generic``; keyword
    args (``metaclass=...``) and empty exprs are dropped.
    """
    base = (base or "").strip()
    if not base or "=" in base:
        return None
    base = base.split("[", 1)[0]  # strip generics/subscripts
    base = base.rsplit(".", 1)[-1]  # last dotted segment
    base = base.strip()
    return base or None


def build_edges(
    files: Iterable[SimpleNamespace], symbols: Iterable[SimpleNamespace]
) -> list[dict]:
    """Compute dependency edges from files + symbols (pure).

    ``files`` items expose ``id``/``path``/``language``; ``symbols`` items expose
    ``id``/``name``/``symbol_type``/``file_id``/``language``/``metadata``.
    """
    files = list(files)
    symbols = list(symbols)
    path_by_id = {f.id: f.path for f in files}
    known_paths = {f.path for f in files}
    id_by_path = {f.path: f.id for f in files}

    # For inheritance resolution: simple class name -> defining class symbol.
    class_by_name: dict[str, SimpleNamespace] = {}
    for s in symbols:
        if s.symbol_type == SymbolType.CLASS:
            class_by_name.setdefault(s.name, s)

    edges: list[dict] = []
    seen: set[tuple] = set()

    def add(edge: dict) -> None:
        key = (
            edge["edge_type"],
            edge.get("source_id") or edge["source_name"],
            edge.get("target_id") or edge["target_name"],
            edge["target_name"],
        )
        if key in seen:
            return
        seen.add(key)
        edges.append(edge)

    for s in symbols:
        meta = s.metadata or {}
        importer_path = path_by_id.get(s.file_id)
        if importer_path is None:
            continue

        if s.symbol_type == SymbolType.IMPORT:
            _import_edge(s, meta, importer_path, known_paths, id_by_path, add)
        elif s.symbol_type == SymbolType.CLASS:
            _inherit_edges(s, meta, importer_path, class_by_name, add)

    return edges


def _import_edge(s, meta, importer_path, known_paths, id_by_path, add) -> None:
    language = (s.language or "").lower()
    if language == "python":
        module = meta.get("module")
        level = int(meta.get("level") or 0)
        target = resolve_python_import(module, level, importer_path, known_paths)
        display = module or "."
    else:  # JavaScript / TypeScript
        module = meta.get("source") or meta.get("module")
        if not module:
            return
        target = resolve_js_import(module, importer_path, known_paths)
        display = module

    if target is not None:
        add(
            {
                "edge_type": EdgeType.IMPORT,
                "source_kind": NodeKind.FILE,
                "source_id": id_by_path.get(importer_path),
                "source_name": importer_path,
                "target_kind": NodeKind.FILE,
                "target_id": id_by_path.get(target),
                "target_name": target,
                "external": False,
                "metadata": {"specifier": display},
            }
        )
    else:
        add(
            {
                "edge_type": EdgeType.IMPORT,
                "source_kind": NodeKind.FILE,
                "source_id": id_by_path.get(importer_path),
                "source_name": importer_path,
                "target_kind": NodeKind.MODULE,
                "target_id": None,
                "target_name": display,
                "external": True,
                "metadata": {"specifier": display},
            }
        )


def _inherit_edges(s, meta, importer_path, class_by_name, add) -> None:
    for base in meta.get("bases", []) or []:
        simple = _base_simple_name(base)
        if not simple:
            continue
        target = class_by_name.get(simple)
        if target is not None and target.id != s.id:
            add(
                {
                    "edge_type": EdgeType.INHERITS,
                    "source_kind": NodeKind.SYMBOL,
                    "source_id": s.id,
                    "source_name": s.name,
                    "target_kind": NodeKind.SYMBOL,
                    "target_id": target.id,
                    "target_name": target.name,
                    "external": False,
                    "metadata": {"file": importer_path},
                }
            )
        else:
            add(
                {
                    "edge_type": EdgeType.INHERITS,
                    "source_kind": NodeKind.SYMBOL,
                    "source_id": s.id,
                    "source_name": s.name,
                    "target_kind": NodeKind.SYMBOL,
                    "target_id": None,
                    "target_name": simple,
                    "external": True,
                    "metadata": {"file": importer_path},
                }
            )


class DependencyService:
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
    ) -> DependencyStats:
        """(Re)build the dependency graph from parsed symbols. Owner-scoped."""
        await self._get_extracted_project(project_id, owner_id)
        files = await self.files.all_for_project(project_id)
        symbols = await self.symbols.all_for_project(
            project_id, symbol_types=[SymbolType.IMPORT, SymbolType.CLASS]
        )
        rows = build_edges(files, symbols)
        # Only replace the edge kinds this phase owns — leave call edges intact.
        await self.edges.replace_for_project(
            project_id, rows, edge_types=[EdgeType.IMPORT, EdgeType.INHERITS]
        )

        by_type: dict[str, int] = {}
        external = 0
        for r in rows:
            key = r["edge_type"].value
            by_type[key] = by_type.get(key, 0) + 1
            if r["external"]:
                external += 1
        stats = DependencyStats(
            edges_total=len(rows),
            internal=len(rows) - external,
            external=external,
            by_type=by_type,
        )
        logger.info(
            "Built dependency graph for %s: %d edges (%d external)",
            project_id,
            stats.edges_total,
            stats.external,
        )
        return stats

    async def get_graph(
        self,
        *,
        project_id: str,
        owner_id: str,
        edge_type: EdgeType | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> tuple[list[GraphEdge], int, dict[str, int]]:
        await self._get_owned_project(project_id, owner_id)
        items = await self.edges.list_for_project(
            project_id, edge_type=edge_type, limit=limit, offset=offset
        )
        total = await self.edges.count_for_project(project_id, edge_type=edge_type)
        breakdown = await self.edges.type_breakdown(project_id)
        return items, total, breakdown

    async def get_neighbors(
        self,
        *,
        project_id: str,
        owner_id: str,
        node: str,
        direction: str = "both",
        edge_type: EdgeType | None = None,
    ) -> tuple[list[GraphEdge], list[GraphEdge]]:
        """Return ``(dependents, dependencies)`` for a node.

        ``dependents`` = edges pointing at the node ("what imports X").
        ``dependencies`` = edges leaving the node ("what X imports").
        """
        await self._get_owned_project(project_id, owner_id)
        dependents: list[GraphEdge] = []
        dependencies: list[GraphEdge] = []
        if direction in ("in", "both"):
            dependents = await self.edges.dependents(
                project_id, node, edge_type=edge_type
            )
        if direction in ("out", "both"):
            dependencies = await self.edges.dependencies(
                project_id, node, edge_type=edge_type
            )
        return dependents, dependencies

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
