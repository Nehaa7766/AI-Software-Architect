"""SQLAlchemy ORM model for the dependency graph (Phase 6).

A ``GraphEdge`` is a directed relationship between two nodes in a project —
a file importing another file, a class inheriting a base, and (reserved for
Phase 7) a function calling another. Kept deliberately generic so the call
graph reuses the same table (shared-model principle).

Nodes are identified by ``*_id`` (a file/symbol row id when the endpoint is
resolved to something inside the project) and/or ``*_name`` (a display label:
a file path, a symbol name, or an unresolved external module). ``external``
marks edges whose target lives outside the project (stdlib, npm, …).
"""
import enum
import uuid

from sqlalchemy import JSON, Boolean, Enum as SAEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


def _uuid() -> str:
    return str(uuid.uuid4())


def _enum_values(enum_cls):
    """Persist enum .value (lowercase) rather than SQLAlchemy's default .name."""
    return [e.value for e in enum_cls]


class EdgeType(str, enum.Enum):
    IMPORT = "import"  # file -> file/module
    INHERITS = "inherits"  # class -> base class
    CALL = "call"  # function -> function (Phase 7)
    DEPENDS = "depends"  # aggregated package/module dependency


class NodeKind(str, enum.Enum):
    FILE = "file"
    SYMBOL = "symbol"
    MODULE = "module"  # unresolved / external module
    PACKAGE = "package"


# One shared SAEnum instance so both node columns reference the same DB type.
_NODE_KIND = SAEnum(NodeKind, name="node_kind", values_callable=_enum_values)


class GraphEdge(Base, TimestampMixin):
    __tablename__ = "graph_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    edge_type: Mapped[EdgeType] = mapped_column(
        SAEnum(EdgeType, name="edge_type", values_callable=_enum_values),
        index=True,
        nullable=False,
    )

    source_kind: Mapped[NodeKind] = mapped_column(_NODE_KIND, nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    source_name: Mapped[str] = mapped_column(String(1024), index=True, nullable=False)

    target_kind: Mapped[NodeKind] = mapped_column(_NODE_KIND, nullable=False)
    target_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    target_name: Mapped[str] = mapped_column(String(1024), index=True, nullable=False)

    # True when the target is outside the project (external dependency).
    external: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    meta: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
