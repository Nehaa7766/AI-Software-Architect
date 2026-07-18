"""Unit tests for the Phase 4 JavaScript/TypeScript parser.

Skipped when ``tree_sitter_language_pack`` (the grammar provider) is not
installed — the parser degrades to a no-op in that case, which is verified
separately in ``test_degrades_without_treesitter``.
"""
from pathlib import Path

import pytest

from app.models.symbol import SymbolType
from app.modules.analysis.services.parsing.javascript_parser import JavaScriptParser


def _grammars_available() -> bool:
    parser = JavaScriptParser()
    return parser._get_parser("TypeScript") is not None


pytestmark = pytest.mark.skipif(
    not _grammars_available(), reason="tree-sitter grammars not installed"
)


def _write(root: Path, rel: str, content: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


TS_SAMPLE = """\
import { useState } from "react";

export interface Props {
  name: string;
}

export enum Color { Red, Green }

export class Button {
  label: string;
  handleClick() { return 1; }
}

export const helper = (x: number) => x * 2;

function standalone() { return 0; }

const MAX = 100;
let counter = 0;
"""


def test_extracts_typescript_symbols(tmp_path: Path):
    path = _write(tmp_path, "app.ts", TS_SAMPLE)
    symbols = JavaScriptParser().parse(path, "TypeScript")
    names_by_type = {}
    for s in symbols:
        names_by_type.setdefault(s.symbol_type, set()).add(s.name)

    assert "Button" in names_by_type.get(SymbolType.CLASS, set())
    assert "Props" in names_by_type.get(SymbolType.INTERFACE, set())
    assert "Color" in names_by_type.get(SymbolType.ENUM, set())
    assert "standalone" in names_by_type.get(SymbolType.FUNCTION, set())
    assert "helper" in names_by_type.get(SymbolType.ARROW_FUNCTION, set())
    assert "handleClick" in names_by_type.get(SymbolType.METHOD, set())
    assert "MAX" in names_by_type.get(SymbolType.CONSTANT, set())


def test_supports_js_and_ts():
    parser = JavaScriptParser()
    assert parser.supports("JavaScript")
    assert parser.supports("TypeScript")
    assert not parser.supports("Python")
