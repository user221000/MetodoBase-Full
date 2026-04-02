"""add plan_json column to planes_generados

Revision ID: 20260402_plan_json
Revises: f8a1b2c3d4e5
Create Date: 2026-04-02 00:00:00.000000

Stores the serialized plan JSON directly in the DB so it survives
container restarts (Railway ephemeral filesystem loses companion files).
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20260402_plan_json"
down_revision: Union[str, None] = "f8a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "planes_generados",
        sa.Column("plan_json", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("planes_generados", "plan_json")
