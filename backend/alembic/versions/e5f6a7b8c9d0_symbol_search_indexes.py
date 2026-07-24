"""symbol search indexes (Phase 5 — symbol index / ranked search)

Adds pg_trgm trigram GIN indexes so case-insensitive substring search
(``name ILIKE '%q%'``) over symbols stays fast on large projects.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-24 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Trigram operators power fast ILIKE '%substring%' lookups.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_index(
        "ix_symbols_name_trgm",
        "symbols",
        ["name"],
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_symbols_parent_trgm",
        "symbols",
        ["parent_symbol"],
        postgresql_using="gin",
        postgresql_ops={"parent_symbol": "gin_trgm_ops"},
    )
    # Composite btree for the common "list this kind in this project" filter.
    op.create_index(
        "ix_symbols_project_type",
        "symbols",
        ["project_id", "symbol_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_symbols_project_type", table_name="symbols")
    op.drop_index("ix_symbols_parent_trgm", table_name="symbols")
    op.drop_index("ix_symbols_name_trgm", table_name="symbols")
    # Leave the pg_trgm extension in place — other objects may rely on it.
