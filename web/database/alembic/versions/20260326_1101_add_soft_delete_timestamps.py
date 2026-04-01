"""add_soft_delete_timestamps

Revision ID: 77162ee0e00c
Revises: 86928e690925
Create Date: 2026-03-26 11:01:51.275034

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77162ee0e00c'
down_revision: Union[str, Sequence[str], None] = '86928e690925'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add soft delete column to clientes
    op.add_column('clientes', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.create_index('ix_clientes_deleted', 'clientes', ['deleted_at'], unique=False, 
                    sqlite_where=sa.text('deleted_at IS NULL'))
    
    # Add soft delete column to usuarios
    op.add_column('usuarios', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.create_index('ix_usuarios_deleted', 'usuarios', ['deleted_at'], unique=False,
                    sqlite_where=sa.text('deleted_at IS NULL'))
    
    # Add soft delete column to planes_generados
    op.add_column('planes_generados', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.create_index('ix_planes_generados_deleted', 'planes_generados', ['deleted_at'], unique=False,
                    sqlite_where=sa.text('deleted_at IS NULL'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_planes_generados_deleted', table_name='planes_generados')
    op.drop_column('planes_generados', 'deleted_at')
    
    op.drop_index('ix_usuarios_deleted', table_name='usuarios')
    op.drop_column('usuarios', 'deleted_at')
    
    op.drop_index('ix_clientes_deleted', table_name='clientes')
    op.drop_column('clientes', 'deleted_at')
