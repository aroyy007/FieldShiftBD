"""Add password authentication and per-farmland equipment.

Revision ID: b904f5e0c3aa
Revises: a7c4e2d91b30
Create Date: 2026-10-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b904f5e0c3aa"
down_revision: Union[str, Sequence[str], None] = "a7c4e2d91b30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("farmers", sa.Column("password_hash", sa.String(length=255), nullable=True))
    op.add_column(
        "farmlands",
        sa.Column(
            "equipment",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    # Preserve equipment already recorded at farmer level when adding the
    # per-farm field. The farmer-level field remains available for onboarding.
    op.execute(
        """UPDATE farmlands AS f
           SET equipment = COALESCE(fp.equipment, '[]'::jsonb)
           FROM farmer_profiles AS fp
           WHERE fp.farmer_id = f.farmer_id"""
    )


def downgrade() -> None:
    op.drop_column("farmlands", "equipment")
    op.drop_column("farmers", "password_hash")
