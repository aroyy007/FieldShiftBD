"""add farmland land type

BARC's published crop land-and-soil conditions (for example, potato and wheat on
high or medium-high land) are stated in terms of the Bangladesh land-type
classes. The M1 farm profile had no field to record land type, so M2 could not
evaluate those conditions for a farm. This additive, nullable column stores the
farmer-reported class; existing rows keep NULL ("not answered").

Revision ID: a7c4e2d91b30
Revises: 163fb0ab6beb
Create Date: 2026-10-08 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7c4e2d91b30'
down_revision: Union[str, Sequence[str], None] = '163fb0ab6beb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('farmlands', sa.Column('land_type', sa.String(length=24), nullable=True))
    op.create_check_constraint(
        'ck_farmlands_land_type',
        'farmlands',
        "land_type IS NULL OR land_type IN "
        "('high', 'medium_high', 'medium_low', 'low', 'very_low')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('ck_farmlands_land_type', 'farmlands', type_='check')
    op.drop_column('farmlands', 'land_type')
