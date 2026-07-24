"""Domain exceptions for the analysis module, mapped to HTTP responses centrally.

Mirrors the projects module's error style (status_code + machine ``code`` +
safe client ``message``) so the central handler can render a consistent body.
"""


class AnalysisError(Exception):
    """Base analysis error carrying an HTTP status and safe client message."""

    status_code: int = 400
    code: str = "analysis_error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.__doc__ or "Analysis error"
        super().__init__(self.message)


class UnsupportedLanguage(AnalysisError):
    """No parser is registered for the requested language."""

    status_code = 422
    code = "unsupported_language"

    def __init__(self, language: str) -> None:
        super().__init__(f"No parser is registered for language '{language}'.")
        self.language = language


class NoParsableFiles(AnalysisError):
    """The project has no files in a language the parsers understand."""

    status_code = 409
    code = "no_parsable_files"


class InvalidFilePath(AnalysisError):
    """The requested file path is empty, absolute, or malformed."""

    status_code = 400
    code = "invalid_file_path"


class PathTraversalBlocked(AnalysisError):
    """The requested path resolves outside the project workspace."""

    status_code = 403
    code = "path_traversal_blocked"


class FileNotFoundInProject(AnalysisError):
    """No such file exists in the project workspace."""

    status_code = 404
    code = "file_not_found"


class FileTooLarge(AnalysisError):
    """The file is too large to open in the viewer."""

    status_code = 413
    code = "file_too_large"


class FileNotViewable(AnalysisError):
    """The file is binary or not decodable as text."""

    status_code = 415
    code = "file_not_viewable"
