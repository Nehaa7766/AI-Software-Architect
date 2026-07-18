"""View layer (presenter) for the scanner — maps file models to response DTOs."""
from app.models.project import ProjectFile
from app.modules.projects.dto.responses import (
    FileListResponse,
    ProjectTreeResponse,
    ScannedFileResponse,
    ScanSummaryResponse,
    TreeNodeResponse,
)
from app.modules.projects.services.tree_service import ProjectTree, TreeNode


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

    @staticmethod
    def tree(tree: ProjectTree) -> ProjectTreeResponse:
        return ProjectTreeResponse(
            root=FileView._node(tree.root),
            total_files=tree.total_files,
            total_dirs=tree.total_dirs,
            truncated=tree.truncated,
        )

    @staticmethod
    def _node(node: TreeNode) -> TreeNodeResponse:
        return TreeNodeResponse(
            name=node.name,
            path=node.path,
            type=node.type,
            size_bytes=node.size_bytes,
            language=node.language,
            children=(
                [FileView._node(c) for c in node.children]
                if node.children is not None
                else None
            ),
        )
