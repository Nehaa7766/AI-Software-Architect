"""Detect frameworks + package managers from manifest files.

Walks the already-collected file list (so it shares the ignore-aware traversal),
reads each recognized manifest, and applies the signature rules. Manifest
reads are size-capped and failure-tolerant — a malformed manifest never aborts
detection.
"""
import json
from collections.abc import Iterable
from pathlib import Path

from app.modules.projects.services.detection.framework_rules import (
    LOCKFILE_PACKAGE_MANAGERS,
    MANIFEST_RULES,
    SUFFIX_MANIFEST_RULES,
    ManifestRule,
)

_MAX_MANIFEST_BYTES = 2 * 1024 * 1024  # don't read absurdly large "manifests"


class FrameworkDetector:
    def __init__(self) -> None:
        self._by_name = {r.filename.lower(): r for r in MANIFEST_RULES}
        self._lockfiles = {k.lower(): v for k, v in LOCKFILE_PACKAGE_MANAGERS.items()}

    def detect(self, files: Iterable[Path]) -> tuple[list[str], list[str]]:
        """Return ``(frameworks, package_managers)`` as sorted unique lists."""
        frameworks: set[str] = set()
        package_managers: set[str] = set()

        for path in files:
            name_lower = path.name.lower()

            if name_lower in self._lockfiles:
                package_managers.add(self._lockfiles[name_lower])

            rule = self._by_name.get(name_lower)
            if rule is not None:
                self._apply_rule(rule, path, frameworks, package_managers)
                continue

            suffix = path.suffix.lower()
            if suffix in SUFFIX_MANIFEST_RULES:
                pm, signatures = SUFFIX_MANIFEST_RULES[suffix]
                if pm:
                    package_managers.add(pm)
                self._scan_text(path, signatures, frameworks)

        return sorted(frameworks), sorted(package_managers)

    def _apply_rule(
        self,
        rule: ManifestRule,
        path: Path,
        frameworks: set[str],
        package_managers: set[str],
    ) -> None:
        if rule.package_manager:
            package_managers.add(rule.package_manager)
        if rule.base_framework:
            frameworks.add(rule.base_framework)
        if not rule.signatures:
            return
        if rule.json_deps:
            self._scan_json_deps(path, rule.signatures, frameworks)
        else:
            self._scan_text(path, rule.signatures, frameworks)

    def _read(self, path: Path) -> str | None:
        try:
            if path.stat().st_size > _MAX_MANIFEST_BYTES:
                return None
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return None

    def _scan_text(
        self, path: Path, signatures: dict[str, str], frameworks: set[str]
    ) -> None:
        text = self._read(path)
        if text is None:
            return
        lowered = text.lower()
        for token, framework in signatures.items():
            if token.lower() in lowered:
                frameworks.add(framework)

    def _scan_json_deps(
        self, path: Path, signatures: dict[str, str], frameworks: set[str]
    ) -> None:
        text = self._read(path)
        if text is None:
            return
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            # Fall back to substring scan if the JSON is malformed.
            self._scan_text(path, signatures, frameworks)
            return
        keys: set[str] = set()
        for section in ("dependencies", "devDependencies", "peerDependencies", "require"):
            block = data.get(section)
            if isinstance(block, dict):
                keys.update(k.lower() for k in block.keys())
        for token, framework in signatures.items():
            token_l = token.lower()
            if any(token_l == k or k.startswith(token_l) for k in keys):
                frameworks.add(framework)
