"""Response DTOs for the analysis module — pure schemas (the View's data shape).

Mapping from ORM models lives in ``views/symbol_view.py``; these classes carry
no mapping logic so the view layer is the single place that turns models into
response bodies.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.symbol import SymbolType, Visibility


class SymbolCounts(BaseModel):
    """The headline symbol counts surfaced in the API/UI (Phase 4 spec §9)."""

    classes: int = 0
    interfaces: int = 0
    enums: int = 0
    functions: int = 0
    methods: int = 0
    variables: int = 0
    constants: int = 0
    imports: int = 0
    exports: int = 0
    decorators: int = 0
    comments: int = 0
    docstrings: int = 0


class ParseSummaryResponse(BaseModel):
    """Result of running (or re-running) the parser on a project."""

    project_id: str
    status: str = "parsed"
    files_total: int
    files_parsed: int
    files_skipped: int
    files_failed: int
    total_symbols: int
    symbols: SymbolCounts
    # Raw per-type counts (superset of ``symbols``) for clients that want detail.
    by_type: dict[str, int]


class SymbolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_id: str
    file_path: str | None = None
    name: str
    symbol_type: SymbolType
    language: str
    parent_symbol: str | None = None
    visibility: Visibility
    signature: str | None = None
    docstring: str | None = None
    line_number: int
    metadata: dict | None = None
    created_at: datetime


class SymbolListResponse(BaseModel):
    symbols: list[SymbolResponse]
    total: int
    by_type: dict[str, int]


class SymbolSummaryResponse(BaseModel):
    project_id: str
    files_parsed: int
    total_symbols: int
    symbols: SymbolCounts
    by_type: dict[str, int]


class FileSymbolCounts(BaseModel):
    """Per-file symbol tally shown against each file in the explorer."""

    functions: int = 0  # standalone functions + arrow functions
    methods: int = 0
    classes: int = 0
    total: int = 0


class SymbolsByFileResponse(BaseModel):
    """Symbol counts per file, keyed by the file's project-relative path."""

    project_id: str
    files: dict[str, FileSymbolCounts]
    total_symbols: int


class FileContentResponse(BaseModel):
    """Read-only source of a single workspace file (Phase 5.1 viewer)."""

    path: str
    language: str
    content: str
