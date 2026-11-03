"""add blood report fields to documents and health_records

Revision ID: b3c91e4f7a20
Revises: a57baa8052d5
Create Date: 2026-10-30 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3c91e4f7a20"
down_revision: Union[str, Sequence[str], None] = "a57baa8052d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adds header fields to documents and reference-range fields to health_records."""
    op.add_column("documents", sa.Column("report_date", sa.Date(), nullable=True))
    op.add_column("documents", sa.Column("lab_name", sa.String(), nullable=True))
    op.add_column("documents", sa.Column("panel_name", sa.String(), nullable=True))

    op.add_column("health_records", sa.Column("panel", sa.String(), nullable=True))
    op.add_column("health_records", sa.Column("printed_low", sa.Float(), nullable=True))
    op.add_column("health_records", sa.Column("printed_high", sa.Float(), nullable=True))


def downgrade() -> None:
    """Removes the fields added in upgrade()."""
    op.drop_column("health_records", "printed_high")
    op.drop_column("health_records", "printed_low")
    op.drop_column("health_records", "panel")

    op.drop_column("documents", "panel_name")
    op.drop_column("documents", "lab_name")
    op.drop_column("documents", "report_date")