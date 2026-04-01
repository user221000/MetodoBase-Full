"""add_gym_settings_table

Revision ID: 2411a87ea6c0
Revises: 57ad7409ccfc
Create Date: 2026-03-26 11:00:57.765448

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2411a87ea6c0'
down_revision: Union[str, Sequence[str], None] = '57ad7409ccfc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('gym_settings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('gym_id', sa.String(length=36), nullable=False),
        sa.Column('trial_days', sa.Integer(), nullable=False, server_default='14'),
        sa.Column('trial_max_clients', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('strict_mode', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='America/Mexico_City'),
        sa.Column('locale', sa.String(length=10), nullable=False, server_default='es_MX'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['gym_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gym_settings_gym_id'), 'gym_settings', ['gym_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_gym_settings_gym_id'), table_name='gym_settings')
    op.drop_table('gym_settings')
