"""ZIP import — validate + stream an uploaded archive to the temp dir.

Streams in chunks so a huge upload never lands fully in memory, and enforces the
size cap as bytes arrive (don't trust the client's Content-Length).
"""
from fastapi import UploadFile

from app.core.config import settings
from app.models.project import ImportSource
from app.modules.projects.services.staging import StagedArchive
from app.modules.projects.services.validator import ProjectValidator
from app.modules.projects.services.workspace_manager import WorkspaceManager
from app.modules.projects.utils.exceptions import FileTooLarge
from app.modules.projects.utils.zip_safety import sanitize_project_name

_CHUNK = 1024 * 1024  # 1 MiB


class ZipImporter:
    def __init__(
        self, *, validator: ProjectValidator, workspace: WorkspaceManager
    ) -> None:
        self.validator = validator
        self.workspace = workspace

    async def stage(self, upload: UploadFile) -> StagedArchive:
        filename = upload.filename or ""
        # Header check on the declared name before reading any bytes.
        if not filename.lower().endswith(".zip"):
            self.validator.validate_zip_upload(filename=filename, size=1)

        tmp_path = self.workspace.new_tmp_file(".zip")
        written = 0
        try:
            with open(tmp_path, "wb") as out:
                while True:
                    chunk = await upload.read(_CHUNK)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > settings.MAX_PROJECT_BYTES:
                        raise FileTooLarge(
                            f"Archive exceeds the "
                            f"{settings.MAX_PROJECT_BYTES // (1024 * 1024)} MB limit."
                        )
                    out.write(chunk)
            # Now that the bytes are on disk: size + integrity validation.
            self.validator.validate_zip_upload(filename=filename, size=written)
            self.validator.validate_zip_file(tmp_path)
        except Exception:
            self.workspace.remove_file(tmp_path)
            raise

        return StagedArchive(
            tmp_path=tmp_path,
            project_name=sanitize_project_name(filename),
            source_type=ImportSource.ZIP,
            source_location=filename,
        )
