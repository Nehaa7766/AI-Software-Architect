"""Detect programming languages by counting source files per language.

Classification order per file: extension -> special filename -> shebang. Files
that match no rule are ignored (data/assets/config noise).
"""
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from app.modules.projects.services.detection.language_rules import (
    EXTENSION_LANGUAGE,
    FILENAME_LANGUAGE,
    NON_PRIMARY_LANGUAGES,
    SHEBANG_LANGUAGE,
)


@dataclass
class LanguageStat:
    language: str
    files: int
    bytes: int
    percentage: float = 0.0


class LanguageDetector:
    def classify(self, path: Path) -> str | None:
        """Return the language for a single file, or None if not source."""
        ext = path.suffix.lower()
        if ext in EXTENSION_LANGUAGE:
            return EXTENSION_LANGUAGE[ext]
        if path.name in FILENAME_LANGUAGE:
            return FILENAME_LANGUAGE[path.name]
        if not ext:
            return self._classify_by_shebang(path)
        return None

    def _classify_by_shebang(self, path: Path) -> str | None:
        try:
            with open(path, "rb") as f:
                first = f.readline(256)
        except OSError:
            return None
        if not first.startswith(b"#!"):
            return None
        line = first.decode("utf-8", "ignore")
        # e.g. "#!/usr/bin/env python3" or "#!/bin/bash"
        for interpreter, language in SHEBANG_LANGUAGE.items():
            if interpreter in line:
                return language
        return None

    def detect(
        self, files: Iterable[Path]
    ) -> tuple[str | None, list[LanguageStat], int]:
        """Return ``(primary_language, sorted_stats, total_source_files)``."""
        counts: dict[str, LanguageStat] = {}
        total_files = 0
        for path in files:
            language = self.classify(path)
            if language is None:
                continue
            try:
                size = path.stat().st_size
            except OSError:
                size = 0
            stat = counts.get(language)
            if stat is None:
                counts[language] = LanguageStat(language=language, files=1, bytes=size)
            else:
                stat.files += 1
                stat.bytes += size
            total_files += 1

        total_bytes = sum(s.bytes for s in counts.values()) or 1
        for stat in counts.values():
            stat.percentage = round(stat.bytes / total_bytes * 100, 2)

        stats = sorted(counts.values(), key=lambda s: (s.files, s.bytes), reverse=True)
        primary = self._pick_primary(stats)
        return primary, stats, total_files

    @staticmethod
    def _pick_primary(stats: list[LanguageStat]) -> str | None:
        """Prefer the top real programming language over markup/styling."""
        for stat in stats:
            if stat.language not in NON_PRIMARY_LANGUAGES:
                return stat.language
        return stats[0].language if stats else None
