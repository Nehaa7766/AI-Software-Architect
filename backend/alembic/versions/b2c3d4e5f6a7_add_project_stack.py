"""add project stack columns (Phase 2 — language/framework detection)

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-27 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("primary_language", sa.String(length=50), nullable=True),
    )
    op.add_column("projects", sa.Column("stack", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "stack")
    op.drop_column("projects", "primary_language")
