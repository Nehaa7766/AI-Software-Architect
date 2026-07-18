"""Phase 4 orchestration — parse a project's files into stored symbols.

Coordinates the parser registry (pick a parser per file), the pluggable parsers
(extract normalized symbols, statically — never executing code), validation +
de-duplication, and the repository (persist). HTTP concerns stay in the
controller; per-file parsing is pure and runs off the event loop in a thread.

Robustness contract: a single unparsable file is logged and skipped so it never
aborts parsing of the rest of the project.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path

from app.models.project import ProjectFile, ProjectStatus
from app.models.symbol import Symbol, SymbolType
from app.modules.analysis.repositories.symbol_repository import SymbolRepository
from app.modules.analysis.services.parsing.base import ParsedSymbol
from app.modules.analysis.services.parsing.registry import ParserRegistry
from app.modules.analysis.utils.exceptions import UnsupportedLanguage
from app.modules.projects.repositories.file_repository import FileRepository
from app.modules.projects.repositories.project_repository import ProjectRepository
from app.modules.projects.utils.exceptions import (
    ProjectNotExtracted,
    ProjectNotFound,
)

logger = logging.getLogger("analysis")

# Skip files above this size — huge generated/minified files blow up parse time
# and symbol counts without adding structural insight.
_MAX_PARSE_BYTES = 2 * 1024 * 1024  # 2 MiB


@dataclass
class ParseStats:
    """Outcome of parsing a project (returned to the controller/view)."""

    files_total: int = 0
    files_parsed: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    total_symbols: int = 0
    by_type: dict[str, int] = field(default_factory=dict)


@dataclass
class _ExtractionResult:
    rows: list[dict]
    files_parsed: int
    files_skipped: int
    files_failed: int


class SymbolService:
    def __init__(
        self,
        *,
        symbols: SymbolRepository,
        files: FileRepository,
        projects: ProjectRepository,
        registry: ParserRegistry | None = None,
    ) -> None:
        self.symbols = symbols
        self.files = files
        self.projects = projects
        self.registry = registry or ParserRegistry()

    # ---- Public API ----
    async def parse_project(self, *, project_id: str, owner_id: str) -> ParseStats:
        """Parse every supported file in an extracted project and store symbols."""
        project = await self._get_extracted_project(project_id, owner_id)
        files = await self.files.all_for_project(project_id)

        # Parsing is CPU/IO-bound and synchronous — keep the event loop free.
        result = await asyncio.to_thread(
            self._extract_all, Path(project.workspace_path), files
        )

        await self.symbols.replace_for_project(project_id, result.rows)

        stats = ParseStats(
            files_total=len(files),
            files_parsed=result.files_parsed,
            files_skipped=result.files_skipped,
            files_failed=result.files_failed,
            total_symbols=len(result.rows),
            by_type=self._count_by_type(result.rows),
        )
        logger.info(
            "Parsed project %s: %d/%d files, %d symbols",
            project_id,
            stats.files_parsed,
            stats.files_total,
            stats.total_symbols,
        )
        return stats

    async def list_symbols(
        self,
        *,
        project_id: str,
        owner_id: str,
        symbol_type: SymbolType | None = None,
        language: str | None = None,
        file_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Symbol], int, dict[str, int]]:
        """List a project's stored symbols (owner-scoped) with paging + breakdown."""
        await self._get_owned_project(project_id, owner_id)  # ownership check
        items = await self.symbols.list_for_project(
            project_id,
            symbol_type=symbol_type,
            language=language,
            file_id=file_id,
            limit=limit,
            offset=offset,
        )
        total = await self.symbols.count_for_project(
            project_id,
            symbol_type=symbol_type,
            language=language,
            file_id=file_id,
        )
        breakdown = await self.symbols.type_breakdown(project_id)
        return items, total, breakdown

    async def counts_by_file(
        self, *, project_id: str, owner_id: str
    ) -> tuple[dict[str, dict[str, int]], int]:
        """Per-file symbol tallies keyed by file path (functions/methods/classes).

        Returns ``({path: {functions, methods, classes, total}}, total_symbols)``.
        """
        await self._get_owned_project(project_id, owner_id)  # ownership check
        rows = await self.symbols.counts_by_file(project_id)
        files = await self.files.all_for_project(project_id)
        id_to_path = {f.id: f.path for f in files}

        out: dict[str, dict[str, int]] = {}
        total = 0
        for file_id, symbol_type, count in rows:
            path = id_to_path.get(file_id)
            if path is None:
                continue  # symbol's file row was removed since parsing
            bucket = out.setdefault(
                path, {"functions": 0, "methods": 0, "classes": 0, "total": 0}
            )
            if symbol_type in (SymbolType.FUNCTION, SymbolType.ARROW_FUNCTION):
                bucket["functions"] += count
            elif symbol_type == SymbolType.METHOD:
                bucket["methods"] += count
            elif symbol_type == SymbolType.CLASS:
                bucket["classes"] += count
            bucket["total"] += count
            total += count
        return out, total

    async def get_summary(
        self, *, project_id: str, owner_id: str
    ) -> tuple[int, int, dict[str, int]]:
        """Return (files_parsed, total_symbols, by_type) for a parsed project."""
        await self._get_owned_project(project_id, owner_id)
        breakdown = await self.symbols.type_breakdown(project_id)
        total = sum(breakdown.values())
        files_parsed = await self.symbols.parsed_file_count(project_id)
        return files_parsed, total, breakdown

    # ---- Pure extraction (runs in a worker thread) ----
    def _extract_all(
        self, workspace_root: Path, files: list[ProjectFile]
    ) -> _ExtractionResult:
        rows: list[dict] = []
        parsed = skipped = failed = 0

        for file in files:
            parser = self._parser_for(file.language)
            if parser is None:
                skipped += 1  # no parser for this language (yet)
                continue

            abs_path = workspace_root / file.path
            try:
                if not abs_path.is_file() or abs_path.stat().st_size > _MAX_PARSE_BYTES:
                    skipped += 1
                    continue
                symbols = parser.parse(abs_path, file.language)
            except SyntaxError as exc:
                failed += 1
                logger.warning("Syntax error parsing %s: %s", file.path, exc)
                continue
            except Exception:  # noqa: BLE001 - one bad file must not abort the run
                failed += 1
                logger.exception("Failed to parse %s; skipping.", file.path)
                continue

            valid = self._validate_and_dedupe(symbols)
            for sym in valid:
                rows.append(self._to_row(file.id, sym))
            parsed += 1

        return _ExtractionResult(
            rows=rows,
            files_parsed=parsed,
            files_skipped=skipped,
            files_failed=failed,
        )

    def _parser_for(self, language: str):
        try:
            return self.registry.get_parser(language)
        except UnsupportedLanguage:
            return None

    @staticmethod
    def _validate_and_dedupe(symbols: list[ParsedSymbol]) -> list[ParsedSymbol]:
        seen: set[tuple] = set()
        out: list[ParsedSymbol] = []
        for sym in symbols:
            if not sym.name or not sym.name.strip():
                continue  # a symbol must have a name
            key = sym.dedupe_key()
            if key in seen:
                continue
            seen.add(key)
            out.append(sym)
        return out

    @staticmethod
    def _to_row(file_id: str, sym: ParsedSymbol) -> dict:
        return {
            "file_id": file_id,
            "name": sym.name[:512],
            "symbol_type": sym.symbol_type,
            "language": sym.language,
            "parent_symbol": sym.parent_symbol[:512] if sym.parent_symbol else None,
            "visibility": sym.visibility,
            "signature": sym.signature[:2048] if sym.signature else None,
            "docstring": sym.docstring[:4096] if sym.docstring else None,
            "line_number": sym.line_number,
            "metadata": sym.metadata or None,
        }

    @staticmethod
    def _count_by_type(rows: list[dict]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in rows:
            key = row["symbol_type"].value
            counts[key] = counts.get(key, 0) + 1
        return counts

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
