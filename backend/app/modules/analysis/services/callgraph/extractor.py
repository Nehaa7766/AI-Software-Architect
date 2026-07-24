"""Language-dispatched call-site extraction (Phase 7)."""
from __future__ import annotations

from app.modules.analysis.services.callgraph.base import CallSite
from app.modules.analysis.services.callgraph.js_calls import extract_js_calls
from app.modules.analysis.services.callgraph.python_calls import extract_python_calls


def extract_calls(source: bytes, language: str) -> list[CallSite]:
    """Extract call sites from ``source`` for a supported language, else ``[]``.

    Malformed sources raise (Python) or return ``[]`` (tree-sitter) — the caller
    turns exceptions into skip-and-continue so one bad file never aborts a build.
    """
    lang = (language or "").lower()
    if lang == "python":
        return extract_python_calls(source.decode("utf-8", errors="replace"))
    if language in ("JavaScript", "TypeScript"):
        return extract_js_calls(source, language)
    return []
