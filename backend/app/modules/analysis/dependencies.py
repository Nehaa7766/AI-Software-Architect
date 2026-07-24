"""FastAPI dependency providers for the analysis module.

Wires the symbol repository + reused project/file repositories and the shared
parser registry per request so controllers stay thin and the dependency graph
is explicit (DIP).
"""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.analysis.repositories.graph_repository import GraphEdgeRepository
from app.modules.analysis.repositories.symbol_repository import SymbolRepository
from app.modules.analysis.services.callgraph_service import CallGraphService
from app.modules.analysis.services.dependency_service import DependencyService
from app.modules.analysis.services.file_viewer_service import FileViewerService
from app.modules.analysis.services.parsing.registry import ParserRegistry
from app.modules.analysis.services.symbol_service import SymbolService
from app.modules.projects.repositories.file_repository import FileRepository
from app.modules.projects.repositories.project_repository import ProjectRepository

DbSession = Annotated[AsyncSession, Depends(get_db)]

# The registry (and its parsers) are stateless/thread-safe to reuse — share one.
_registry = ParserRegistry()


def get_symbol_repository(db: DbSession) -> SymbolRepository:
    return SymbolRepository(db)


def get_symbol_service(
    symbols: Annotated[SymbolRepository, Depends(get_symbol_repository)],
    db: DbSession,
) -> SymbolService:
    return SymbolService(
        symbols=symbols,
        files=FileRepository(db),
        projects=ProjectRepository(db),
        registry=_registry,
    )


def get_file_viewer_service(db: DbSession) -> FileViewerService:
    return FileViewerService(projects=ProjectRepository(db))


def get_dependency_service(db: DbSession) -> DependencyService:
    return DependencyService(
        edges=GraphEdgeRepository(db),
        symbols=SymbolRepository(db),
        files=FileRepository(db),
        projects=ProjectRepository(db),
    )


def get_callgraph_service(db: DbSession) -> CallGraphService:
    return CallGraphService(
        edges=GraphEdgeRepository(db),
        symbols=SymbolRepository(db),
        files=FileRepository(db),
        projects=ProjectRepository(db),
    )
