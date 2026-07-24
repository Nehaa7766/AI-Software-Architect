"""Resolve import statements to internal project files (Phase 6).

Pure, filesystem-free: given the set of known project file paths (POSIX,
workspace-relative), map a Python/JS/TS import to the file it refers to, or
``None`` when it points outside the project (stdlib / third-party). Unit-tested
in isolation — the dependency service supplies the path set.
"""
from __future__ import annotations

# Extensions tried when a JS/TS relative import omits one, in priority order.
_JS_EXTS = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte"]


def _normalize_posix(path: str) -> str:
    """Collapse ``.`` and ``..`` segments in a POSIX path (no leading slash)."""
    parts: list[str] = []
    for seg in path.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if parts and parts[-1] != "..":
                parts.pop()
            else:
                parts.append("..")
        else:
            parts.append(seg)
    return "/".join(parts)


def _parent(path: str) -> str:
    return path.rsplit("/", 1)[0] if "/" in path else ""


def _first_known(candidates: list[str], known: set[str]) -> str | None:
    for c in candidates:
        c = _normalize_posix(c)
        if c in known:
            return c
    return None


def _match_suffix(fragment: str, known: set[str]) -> str | None:
    """Find an internal file for an absolute module (tolerant of a src/ root).

    Tries an exact path first, then the shortest known path ending in the
    fragment — so ``app.services.x`` matches ``src/app/services/x.py`` even when
    the package root isn't the workspace root.
    """
    if fragment in known:
        return fragment
    matches = [p for p in known if p == fragment or p.endswith("/" + fragment)]
    if not matches:
        return None
    # Deterministic: shortest path (closest to root), then alphabetical.
    return sorted(matches, key=lambda p: (p.count("/"), len(p), p))[0]


def resolve_python_import(
    module: str | None,
    level: int,
    importer_path: str,
    known_paths: set[str],
) -> str | None:
    """Resolve a Python import to an internal file path, or ``None`` if external.

    ``level`` is the relative-import dot count (0 = absolute). ``module`` is the
    dotted module ("a.b.c") or None for ``from . import x``.
    """
    if level and level > 0:
        # Relative: start from the importer's package directory, ascend
        # (level - 1) more, then descend through the module parts.
        base = _parent(importer_path)
        for _ in range(level - 1):
            base = _parent(base)
        parts = module.split(".") if module else []
        target = "/".join([base, *parts]) if base else "/".join(parts)
        if not parts:  # from . import x  -> the package __init__
            return _first_known([f"{base}/__init__.py"], known_paths)
        return _first_known(
            [f"{target}.py", f"{target}/__init__.py"], known_paths
        )

    if not module:
        return None
    frag = "/".join(module.split("."))
    return _match_suffix(f"{frag}.py", known_paths) or _match_suffix(
        f"{frag}/__init__.py", known_paths
    )


def resolve_js_import(
    source: str, importer_path: str, known_paths: set[str]
) -> str | None:
    """Resolve a JS/TS import specifier to an internal file, or ``None``.

    Only relative specifiers (``./`` , ``../``) can be internal; bare specifiers
    ("react", "@scope/pkg") are third-party and return ``None``.
    """
    if not source.startswith("."):
        return None
    base = _parent(importer_path)
    joined = _normalize_posix(f"{base}/{source}" if base else source)

    candidates: list[str] = []
    # If the specifier already carries a known extension, try it directly.
    if any(joined.endswith(ext) for ext in _JS_EXTS):
        candidates.append(joined)
    # ./foo -> ./foo.ts, ./foo.tsx, ...
    candidates += [f"{joined}{ext}" for ext in _JS_EXTS]
    # ./foo -> ./foo/index.ts, ...
    candidates += [f"{joined}/index{ext}" for ext in _JS_EXTS]
    return _first_known(candidates, known_paths)
