"""Extract function/method call sites from Python source via ``ast``.

Never executes code. For each call expression we record the *enclosing* function
(and its class, for methods) and the *callee* name, so the call-graph service can
resolve caller and callee to symbol rows.
"""
from __future__ import annotations

import ast

from app.modules.analysis.services.callgraph.base import CallSite


def _callee_name(func: ast.expr) -> str | None:
    """The called name: ``foo()`` -> foo, ``a.b.foo()`` / ``self.foo()`` -> foo."""
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None  # calls on subscripts/lambdas/etc. are unresolvable


class _Collector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.calls: list[CallSite] = []
        # Stacks of enclosing (function, class) scopes.
        self._funcs: list[str] = []
        self._classes: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._classes.append(node.name)
        self.generic_visit(node)
        self._classes.pop()

    def _visit_func(self, node) -> None:
        self._funcs.append(node.name)
        self.generic_visit(node)
        self._funcs.pop()

    visit_FunctionDef = _visit_func
    visit_AsyncFunctionDef = _visit_func

    def visit_Call(self, node: ast.Call) -> None:
        if self._funcs:  # only calls made from inside a function are edges
            callee = _callee_name(node.func)
            if callee:
                self.calls.append(
                    CallSite(
                        caller=self._funcs[-1],
                        caller_parent=self._classes[-1] if self._classes else None,
                        callee=callee,
                        line=getattr(node, "lineno", 0),
                    )
                )
        self.generic_visit(node)


def extract_python_calls(source: str) -> list[CallSite]:
    """Return all in-function call sites in a Python source string."""
    tree = ast.parse(source)  # does NOT execute the code
    collector = _Collector()
    collector.visit(tree)
    return collector.calls
