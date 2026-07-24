"""add graph_edges table (Phase 6 — dependency graph)

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-24 15:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_EDGE_TYPE = sa.Enum("import", "inherits", "call", "depends", name="edge_type")
_NODE_KIND = sa.Enum("file", "symbol", "module", "package", name="node_kind")


def upgrade() -> None:
    op.create_table(
        "graph_edges",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("edge_type", _EDGE_TYPE, nullable=False),
        sa.Column("source_kind", _NODE_KIND, nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=True),
        sa.Column("source_name", sa.String(length=1024), nullable=False),
        sa.Column("target_kind", _NODE_KIND, nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=True),
        sa.Column("target_name", sa.String(length=1024), nullable=False),
        sa.Column("external", sa.Boolean(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_graph_edges_project_id"), "graph_edges", ["project_id"]
    )
    op.create_index(op.f("ix_graph_edges_edge_type"), "graph_edges", ["edge_type"])
    op.create_index(op.f("ix_graph_edges_source_id"), "graph_edges", ["source_id"])
    op.create_index(op.f("ix_graph_edges_target_id"), "graph_edges", ["target_id"])
    op.create_index(
        op.f("ix_graph_edges_source_name"), "graph_edges", ["source_name"]
    )
    op.create_index(
        op.f("ix_graph_edges_target_name"), "graph_edges", ["target_name"]
    )
    # Traversal hot paths: "edges of this type into/out of a node in a project".
    op.create_index(
        "ix_graph_edges_project_type", "graph_edges", ["project_id", "edge_type"]
    )


def downgrade() -> None:
    op.drop_index("ix_graph_edges_project_type", table_name="graph_edges")
    op.drop_index(op.f("ix_graph_edges_target_name"), table_name="graph_edges")
    op.drop_index(op.f("ix_graph_edges_source_name"), table_name="graph_edges")
    op.drop_index(op.f("ix_graph_edges_target_id"), table_name="graph_edges")
    op.drop_index(op.f("ix_graph_edges_source_id"), table_name="graph_edges")
    op.drop_index(op.f("ix_graph_edges_edge_type"), table_name="graph_edges")
    op.drop_index(op.f("ix_graph_edges_project_id"), table_name="graph_edges")
    op.drop_table("graph_edges")
    _NODE_KIND.drop(op.get_bind(), checkfirst=True)
    _EDGE_TYPE.drop(op.get_bind(), checkfirst=True)
