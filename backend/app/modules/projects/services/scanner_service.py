"""Project scanner (Phase 3) — build a per-file inventory of source files.

Traverses the extracted workspace (ignore-aware), keeps only files that classify
to a supported language, and records each file's relative path, language, size,
and SHA-256 content hash. Pure logic: returns plain dicts; persistence is the
repository's job and orchestration is the project service's.
"""
import hashlib
from dataclasses import dataclass
from pathlib import Path

from app.modules.projects.services.detection.language_detector import LanguageDetector
from app.modules.projects.utils.ignore_rules import walk_files

_HASH_CHUNK = 1024 * 1024  # 1 MiB


@dataclass
class ScannedFile:
    path: str  # relative, POSIX-separated
    language: str
    size_bytes: int
    content_hash: str


@dataclass
class ScanResult:
    files: list[ScannedFile]
    by_language: dict[str, int]

    @property
    def total_files(self) -> int:
        return len(self.files)


class ScannerService:
    def __init__(self, languages: LanguageDetector | None = None) -> None:
        self.languages = languages or LanguageDetector()

    def scan(self, project_root: Path | str) -> ScanResult:
        root = Path(project_root)
        files: list[ScannedFile] = []
        by_language: dict[str, int] = {}

        for abs_path in walk_files(root):
            language = self.languages.classify(abs_path)
            if language is None:
                continue  # only supported source files are inventoried
            try:
                size = abs_path.stat().st_size
                digest = self._hash_file(abs_path)
            except OSError:
                continue  # unreadable file — skip rather than abort the scan
            rel = abs_path.relative_to(root).as_posix()
            files.append(
                ScannedFile(
                    path=rel,
                    language=language,
                    size_bytes=size,
                    content_hash=digest,
                )
            )
            by_language[language] = by_language.get(language, 0) + 1

        files.sort(key=lambda f: f.path)
        return ScanResult(files=files, by_language=by_language)

    @staticmethod
    def _hash_file(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(_HASH_CHUNK):
                h.update(chunk)
        return h.hexdigest()
