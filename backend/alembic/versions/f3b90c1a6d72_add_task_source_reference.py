"""Add stable source references for idempotent task ingestion.

Revision ID: f3b90c1a6d72
Revises: 03d81c981e6b
Create Date: 2026-10-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3b90c1a6d72"
down_revision: Union[str, Sequence[str], None] = "03d81c981e6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("source_reference", sa.String(length=200)))
    op.create_index(
        "uq_tasks_season_source_reference",
        "tasks",
        ["season_id", "source_reference"],
        unique=True,
        postgresql_where=sa.text("source_reference IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_tasks_season_source_reference", table_name="tasks")
    op.drop_column("tasks", "source_reference")
