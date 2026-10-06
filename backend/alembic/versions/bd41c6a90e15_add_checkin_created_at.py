"""Add the creation timestamp to farmer check-ins.

Revision ID: bd41c6a90e15
Revises: f3b90c1a6d72
Create Date: 2026-10-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "bd41c6a90e15"
down_revision: Union[str, Sequence[str], None] = "f3b90c1a6d72"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "farm_checkins",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("farm_checkins", "created_at")
