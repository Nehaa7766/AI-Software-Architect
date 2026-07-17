"""Domain exceptions for the projects module, mapped to HTTP responses centrally."""


class ProjectError(Exception):
    """Base project error carrying an HTTP status and safe client message."""

    status_code: int = 400
    code: str = "project_error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.__doc__ or "Project error"
        super().__init__(self.message)


class InvalidArchive(ProjectError):
    """The uploaded file is not a valid ZIP archive."""

    status_code = 400
    code = "invalid_archive"


class UnsupportedFileType(ProjectError):
    """Only ZIP archives are accepted."""

    status_code = 415
    code = "unsupported_file_type"


class FileTooLarge(ProjectError):
    """The uploaded file exceeds the maximum allowed size."""

    status_code = 413
    code = "file_too_large"


class UnsafeArchive(ProjectError):
    """The archive contains unsafe paths (path traversal / zip slip)."""

    status_code = 400
    code = "unsafe_archive"


class ExtractionFailed(ProjectError):
    """The archive could not be extracted."""

    status_code = 400
    code = "extraction_failed"


class InvalidGitHubUrl(ProjectError):
    """The GitHub repository URL is invalid."""

    status_code = 400
    code = "invalid_github_url"


class RepositoryUnavailable(ProjectError):
    """The GitHub repository is private, missing, or unreachable."""

    status_code = 400
    code = "repository_unavailable"


class ProjectNotFound(ProjectError):
    """The requested project does not exist."""

    status_code = 404
    code = "project_not_found"


class ProjectNotExtracted(ProjectError):
    """The project has not been extracted yet, so it cannot be analyzed."""

    status_code = 409
    code = "project_not_extracted"
