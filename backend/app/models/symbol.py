"""SQLAlchemy ORM model for extracted code symbols (Phase 4 — AST parsing).

A ``Symbol`` row is a single language-independent structural element discovered
by statically parsing a source file (a class, function, method, import, …). The
parsers never execute user code; they only read and analyze it. All languages
normalize to this one shape so downstream phases stay language-agnostic.
"""
import enum
import uuid

from sqlalchemy import JSON, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


def _uuid() -> str:
    return str(uuid.uuid4())


class SymbolType(str, enum.Enum):
    """Normalized, language-independent kind of a code symbol.

    New languages map their native constructs onto these members; the set is
    intentionally broad so Java/Go/C#/PHP parsers can be added without schema
    changes (open/closed principle).
    """

    CLASS = "class"
    INTERFACE = "interface"
    STRUCT = "struct"
    ENUM = "enum"
    FUNCTION = "function"
    ARROW_FUNCTION = "arrow_function"
    METHOD = "method"
    PROPERTY = "property"
    VARIABLE = "variable"
    CONSTANT = "constant"
    IMPORT = "import"
    EXPORT = "export"
    DECORATOR = "decorator"
    NAMESPACE = "namespace"
    PACKAGE = "package"
    COMMENT = "comment"
    DOCSTRING = "docstring"
    TYPE_ALIAS = "type_alias"


class Visibility(str, enum.Enum):
    PUBLIC = "public"
    PROTECTED = "protected"
    PRIVATE = "private"


class Symbol(Base, TimestampMixin):
    __tablename__ = "symbols"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    file_id: Mapped[str] = mapped_column(
        ForeignKey("project_files.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    symbol_type: Mapped[SymbolType] = mapped_column(
        # values_callable makes SQLAlchemy persist the member .value ("class")
        # rather than the default .name ("CLASS"), matching the enum created in
        # the migration.
        SAEnum(
            SymbolType,
            name="symbol_type",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        index=True,
        nullable=False,
    )
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    # Name of the enclosing symbol (e.g. the class a method lives in), or None.
    parent_symbol: Mapped[str | None] = mapped_column(String(512), nullable=True)
    visibility: Mapped[Visibility] = mapped_column(
        SAEnum(
            Visibility,
            name="symbol_visibility",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=Visibility.PUBLIC,
        nullable=False,
    )
    # Reconstructed declaration, e.g. "def foo(a, b) -> int" — never executed.
    signature: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    docstring: Mapped[str | None] = mapped_column(String(4096), nullable=True)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Language-specific extras (decorators, base classes, is_async, exported, …).
    # JSON so parsers can enrich without a migration per attribute.
    meta: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    project: Mapped["Project"] = relationship()  # noqa: F821
    file: Mapped["ProjectFile"] = relationship()  # noqa: F821
