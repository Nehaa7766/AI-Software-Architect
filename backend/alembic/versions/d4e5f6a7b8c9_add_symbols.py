"""add symbols table (Phase 4 — AST parsing)

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-17 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_SYMBOL_TYPE = sa.Enum(
    "class",
    "interface",
    "struct",
    "enum",
    "function",
    "arrow_function",
    "method",
    "property",
    "variable",
    "constant",
    "import",
    "export",
    "decorator",
    "namespace",
    "package",
    "comment",
    "docstring",
    "type_alias",
    name="symbol_type",
)
_VISIBILITY = sa.Enum("public", "protected", "private", name="symbol_visibility")


def upgrade() -> None:
    op.create_table(
        "symbols",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("file_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("symbol_type", _SYMBOL_TYPE, nullable=False),
        sa.Column("language", sa.String(length=50), nullable=False),
        sa.Column("parent_symbol", sa.String(length=512), nullable=True),
        sa.Column("visibility", _VISIBILITY, nullable=False),
        sa.Column("signature", sa.String(length=2048), nullable=True),
        sa.Column("docstring", sa.String(length=4096), nullable=True),
        sa.Column("line_number", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["file_id"], ["project_files.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_symbols_project_id"), "symbols", ["project_id"], unique=False
    )
    op.create_index(op.f("ix_symbols_file_id"), "symbols", ["file_id"], unique=False)
    op.create_index(
        op.f("ix_symbols_symbol_type"), "symbols", ["symbol_type"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_symbols_symbol_type"), table_name="symbols")
    op.drop_index(op.f("ix_symbols_file_id"), table_name="symbols")
    op.drop_index(op.f("ix_symbols_project_id"), table_name="symbols")
    op.drop_table("symbols")
    _VISIBILITY.drop(op.get_bind(), checkfirst=True)
    _SYMBOL_TYPE.drop(op.get_bind(), checkfirst=True)
