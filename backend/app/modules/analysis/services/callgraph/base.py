"""Shared types for call extraction."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CallSite:
    """A single call expression found inside a function/method body."""

    caller: str  # enclosing function/method name
    caller_parent: str | None  # enclosing class (for methods), else None
    callee: str  # called name (simple, last attribute segment)
    line: int
