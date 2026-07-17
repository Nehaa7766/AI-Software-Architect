"""add projects table (Phase 1 — project import)

Revision ID: a1b2c3d4e5f6
Revises: 656ee638c105
Create Date: 2026-06-27 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "656ee638c105"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("project_name", sa.String(length=255), nullable=False),
        sa.Column(
            "source_type",
            sa.Enum("ZIP", "GITHUB", name="import_source"),
            nullable=False,
        ),
        sa.Column("source_location", sa.String(length=1024), nullable=False),
        sa.Column("workspace_path", sa.String(length=1024), nullable=True),
        sa.Column(
            "status",
            sa.Enum("UPLOADED", "EXTRACTED", "FAILED", name="project_status"),
            nullable=False,
        ),
        sa.Column("error_message", sa.String(length=1024), nullable=True),
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
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_projects_owner_id"), "projects", ["owner_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_projects_owner_id"), table_name="projects")
    op.drop_table("projects")
    # Drop the enum types created alongside the table (Postgres).
    sa.Enum(name="project_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="import_source").drop(op.get_bind(), checkfirst=True)
