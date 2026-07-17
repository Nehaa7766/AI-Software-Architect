"""Orchestrate language + framework detection over an extracted project.

Walks the workspace once (ignore-aware) and feeds the file list to both
detectors, so detection costs a single traversal. Returns a plain dict ready to
persist on ``Project.stack`` and serialize to the client.
"""
from pathlib import Path

from app.modules.projects.services.detection.framework_detector import FrameworkDetector
from app.modules.projects.services.detection.language_detector import LanguageDetector
from app.modules.projects.utils.ignore_rules import walk_files


class DetectionService:
    def __init__(
        self,
        *,
        languages: LanguageDetector | None = None,
        frameworks: FrameworkDetector | None = None,
    ) -> None:
        self.languages = languages or LanguageDetector()
        self.frameworks = frameworks or FrameworkDetector()

    def detect(self, project_root: Path | str) -> dict:
        root = Path(project_root)
        # Materialize once — both detectors iterate the same list.
        files = list(walk_files(root))

        primary, stats, total_files = self.languages.detect(files)
        frameworks, package_managers = self.frameworks.detect(files)

        return {
            "primary_language": primary,
            "languages": [
                {
                    "language": s.language,
                    "files": s.files,
                    "bytes": s.bytes,
                    "percentage": s.percentage,
                }
                for s in stats
            ],
            "frameworks": frameworks,
            "package_managers": package_managers,
            "total_files": total_files,
            "total_source_bytes": sum(s.bytes for s in stats),
        }
