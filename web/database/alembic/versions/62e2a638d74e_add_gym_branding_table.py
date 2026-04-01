"""add_gym_branding_table

Revision ID: 62e2a638d74e
Revises: c4f8e9d2a3b1
Create Date: 2026-03-25 17:26:07.521606

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62e2a638d74e'
down_revision: Union[str, Sequence[str], None] = 'c4f8e9d2a3b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('gym_branding',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('gym_id', sa.String(length=36), nullable=False),
    sa.Column('nombre_gym', sa.String(length=255), nullable=False),
    sa.Column('nombre_corto', sa.String(length=100), nullable=False),
    sa.Column('tagline', sa.String(length=255), nullable=False),
    sa.Column('telefono', sa.String(length=30), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('whatsapp', sa.String(length=30), nullable=False),
    sa.Column('direccion_linea1', sa.String(length=255), nullable=False),
    sa.Column('direccion_linea2', sa.String(length=255), nullable=False),
    sa.Column('direccion_linea3', sa.String(length=255), nullable=False),
    sa.Column('instagram', sa.String(length=100), nullable=False),
    sa.Column('facebook', sa.String(length=255), nullable=False),
    sa.Column('tiktok', sa.String(length=100), nullable=False),
    sa.Column('cuota_mensual', sa.Float(), nullable=False),
    sa.Column('logo_path', sa.String(length=500), nullable=False),
    sa.Column('color_primario', sa.String(length=7), nullable=False),
    sa.Column('color_secundario', sa.String(length=7), nullable=False),
    sa.ForeignKeyConstraint(['gym_id'], ['usuarios.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gym_branding_gym_id'), 'gym_branding', ['gym_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_gym_branding_gym_id'), table_name='gym_branding')
    op.drop_table('gym_branding')
