"""add_license_activations_checkout_sessions_fiscal_fields

Revision ID: a19a0ae3ac49
Revises: 62e2a638d74e
Create Date: 2026-03-25 19:28:44.651097

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a19a0ae3ac49'
down_revision: Union[str, Sequence[str], None] = '62e2a638d74e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # H-02: license_activations table
    op.create_table('license_activations',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('hardware_id', sa.String(length=128), nullable=False),
    sa.Column('clave_hash', sa.String(length=64), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('plan', sa.String(length=30), nullable=False),
    sa.Column('activa', sa.Boolean(), nullable=True),
    sa.Column('revocada', sa.Boolean(), nullable=True),
    sa.Column('expira', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_license_activations_email', 'license_activations', ['email'], unique=False)
    op.create_index(op.f('ix_license_activations_hardware_id'), 'license_activations', ['hardware_id'], unique=True)

    # H-10: checkout_sessions table
    op.create_table('checkout_sessions',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('gym_id', sa.String(length=36), nullable=False),
    sa.Column('stripe_session_id', sa.String(length=255), nullable=True),
    sa.Column('plan', sa.String(length=30), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['gym_id'], ['usuarios.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('stripe_session_id')
    )
    op.create_index(op.f('ix_checkout_sessions_gym_id'), 'checkout_sessions', ['gym_id'], unique=False)

    # H-14: fiscal fields on gym_profiles
    op.add_column('gym_profiles', sa.Column('razon_social', sa.String(length=255), nullable=True))
    op.add_column('gym_profiles', sa.Column('regimen_fiscal', sa.String(length=10), nullable=True))
    op.add_column('gym_profiles', sa.Column('codigo_postal_fiscal', sa.String(length=5), nullable=True))
    op.add_column('gym_profiles', sa.Column('uso_cfdi', sa.String(length=10), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # H-14
    op.drop_column('gym_profiles', 'uso_cfdi')
    op.drop_column('gym_profiles', 'codigo_postal_fiscal')
    op.drop_column('gym_profiles', 'regimen_fiscal')
    op.drop_column('gym_profiles', 'razon_social')
    # H-10
    op.drop_index(op.f('ix_checkout_sessions_gym_id'), table_name='checkout_sessions')
    op.drop_table('checkout_sessions')
    # H-02
    op.drop_index(op.f('ix_license_activations_hardware_id'), table_name='license_activations')
    op.drop_index('ix_license_activations_email', table_name='license_activations')
    op.drop_table('license_activations')
