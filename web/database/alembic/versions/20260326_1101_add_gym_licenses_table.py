"""add_gym_licenses_table

Revision ID: ae1e9e68e9c0
Revises: 2411a87ea6c0
Create Date: 2026-03-26 11:01:14.690781

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae1e9e68e9c0'
down_revision: Union[str, Sequence[str], None] = '2411a87ea6c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('gym_licenses',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('gym_id', sa.String(length=36), nullable=False),
        sa.Column('license_key', sa.String(length=255), nullable=False),
        sa.Column('plan_tier', sa.String(length=20), nullable=False),
        sa.Column('max_clients', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('payment_provider', sa.String(length=20), nullable=True),
        sa.Column('payment_reference', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['gym_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gym_licenses_gym_id'), 'gym_licenses', ['gym_id'], unique=False)
    op.create_index(op.f('ix_gym_licenses_license_key'), 'gym_licenses', ['license_key'], unique=True)
    op.create_index('ix_gym_licenses_active', 'gym_licenses', ['is_active', 'expires_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_gym_licenses_active', table_name='gym_licenses')
    op.drop_index(op.f('ix_gym_licenses_license_key'), table_name='gym_licenses')
    op.drop_index(op.f('ix_gym_licenses_gym_id'), table_name='gym_licenses')
    op.drop_table('gym_licenses')
