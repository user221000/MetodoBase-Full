"""add_horarios_comidas_gym

Revision ID: 57ad7409ccfc
Revises: 6731d0d2d7d5
Create Date: 2026-03-26 10:36:46.138645

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '57ad7409ccfc'
down_revision: Union[str, Sequence[str], None] = '6731d0d2d7d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('gym_profiles', sa.Column('horarios_comidas', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('gym_profiles', 'horarios_comidas')
