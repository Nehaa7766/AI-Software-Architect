"""View layer (presenter) for analysis — maps symbol models/stats to DTOs."""
from app.models.symbol import Symbol
from app.modules.analysis.dto.responses import (
    FileSymbolCounts,
    ParseSummaryResponse,
    SymbolCounts,
    SymbolListResponse,
    SymbolResponse,
    SymbolsByFileResponse,
    SymbolSummaryResponse,
)
from app.modules.analysis.services.symbol_service import ParseStats


class SymbolView:
    """Presents parsed-symbol models and stats as response DTOs (model -> view)."""

    @staticmethod
    def _counts(by_type: dict[str, int]) -> SymbolCounts:
        # Arrow functions count toward "functions"; type aliases are grouped
        # loosely under nothing headline (still visible in ``by_type``).
        return SymbolCounts(
            classes=by_type.get("class", 0),
            interfaces=by_type.get("interface", 0),
            enums=by_type.get("enum", 0),
            functions=by_type.get("function", 0) + by_type.get("arrow_function", 0),
            methods=by_type.get("method", 0),
            variables=by_type.get("variable", 0),
            constants=by_type.get("constant", 0),
            imports=by_type.get("import", 0),
            exports=by_type.get("export", 0),
            decorators=by_type.get("decorator", 0),
            comments=by_type.get("comment", 0),
            docstrings=by_type.get("docstring", 0),
        )

    @staticmethod
    def summary(project_id: str, stats: ParseStats) -> ParseSummaryResponse:
        return ParseSummaryResponse(
            project_id=project_id,
            status="parsed",
            files_total=stats.files_total,
            files_parsed=stats.files_parsed,
            files_skipped=stats.files_skipped,
            files_failed=stats.files_failed,
            total_symbols=stats.total_symbols,
            symbols=SymbolView._counts(stats.by_type),
            by_type=stats.by_type,
        )

    @staticmethod
    def project_summary(
        project_id: str, files_parsed: int, total: int, by_type: dict[str, int]
    ) -> SymbolSummaryResponse:
        return SymbolSummaryResponse(
            project_id=project_id,
            files_parsed=files_parsed,
            total_symbols=total,
            symbols=SymbolView._counts(by_type),
            by_type=by_type,
        )

    @staticmethod
    def _to_response(symbol: Symbol) -> SymbolResponse:
        return SymbolResponse(
            id=symbol.id,
            file_id=symbol.file_id,
            name=symbol.name,
            symbol_type=symbol.symbol_type,
            language=symbol.language,
            parent_symbol=symbol.parent_symbol,
            visibility=symbol.visibility,
            signature=symbol.signature,
            docstring=symbol.docstring,
            line_number=symbol.line_number,
            metadata=symbol.meta,  # ORM attr is ``meta`` (column "metadata")
            created_at=symbol.created_at,
        )

    @staticmethod
    def by_file(
        project_id: str, files: dict[str, dict[str, int]], total: int
    ) -> SymbolsByFileResponse:
        return SymbolsByFileResponse(
            project_id=project_id,
            files={
                path: FileSymbolCounts(**counts) for path, counts in files.items()
            },
            total_symbols=total,
        )

    @staticmethod
    def collection(
        symbols: list[Symbol], total: int, by_type: dict[str, int]
    ) -> SymbolListResponse:
        return SymbolListResponse(
            symbols=[SymbolView._to_response(s) for s in symbols],
            total=total,
            by_type=by_type,
        )
