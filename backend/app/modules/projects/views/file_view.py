"""View layer (presenter) for the scanner — maps file models to response DTOs."""
from app.models.project import ProjectFile
from app.modules.projects.dto.responses import (
    FileListResponse,
    ScannedFileResponse,
    ScanSummaryResponse,
)


class FileView:
    """Presents scanned-file models as response DTOs (model -> view)."""

    @staticmethod
    def summary(total_files: int, by_language: dict[str, int]) -> ScanSummaryResponse:
        return ScanSummaryResponse(total_files=total_files, by_language=by_language)

    @staticmethod
    def collection(
        files: list[ProjectFile], total: int, by_language: dict[str, int]
    ) -> FileListResponse:
        return FileListResponse(
            files=[ScannedFileResponse.model_validate(f) for f in files],
            total=total,
            by_language=by_language,
        )
