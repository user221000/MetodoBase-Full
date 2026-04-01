"""add_auth_audit_log_table

Revision ID: 86928e690925
Revises: ae1e9e68e9c0
Create Date: 2026-03-26 11:01:34.201627

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86928e690925'
down_revision: Union[str, Sequence[str], None] = 'ae1e9e68e9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('auth_audit_log',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('gym_id', sa.String(length=36), nullable=True),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),  # IPv6 max length
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(length=36), nullable=True),
        sa.Column('event_metadata', sa.JSON(), nullable=True),  # renamed from 'metadata' to avoid SQLAlchemy reserved word
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['gym_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_auth_audit_gym', 'auth_audit_log', ['gym_id', 'created_at'], unique=False)
    op.create_index('ix_auth_audit_user', 'auth_audit_log', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_auth_audit_type', 'auth_audit_log', ['event_type', 'created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_auth_audit_type', table_name='auth_audit_log')
    op.drop_index('ix_auth_audit_user', table_name='auth_audit_log')
    op.drop_index('ix_auth_audit_gym', table_name='auth_audit_log')
    op.drop_table('auth_audit_log')
