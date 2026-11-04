"""drop users role column

Revision ID: "d7e2a1c9f003"
Revises: b3c91e4f7a20
Create Date: 2026-11-04 12:12:09.102703

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "d7e2a1c9f003"
down_revision: Union[str, Sequence[str], None] = "b3c91e4f7a20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Removes the role column. Every account is a patient, so it is no longer needed."""
    op.drop_column("users", "role")


def downgrade() -> None:
    """Adds the role column back, filling existing accounts with 'patient'."""
    op.add_column(
        "users",
        sa.Column("role", sa.String(), nullable=False, server_default="patient"),
    )