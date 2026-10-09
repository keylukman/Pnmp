"""add devices.polling_interval_seconds and set monitoring_enabled default false

Revision ID: 20261009_0001
Revises:
Create Date: 2026-10-09 (Phase 3 Step 8)

Idempotent: checks the current PostgreSQL schema before ALTER so it is safe to
run against databases created via create_all (which may already contain the
column). Does NOT modify existing rows — devices that were previously enabled
stay enabled; only the DEFAULT for newly inserted rows changes.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "20261009_0001"
down_revision = None
branch_labels = None
depends_on = None


def _column_exists(inspector, table, column):
    return any(c["name"] == column for c in inspector.get_columns(table))


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "devices" not in inspector.get_table_names():
        return  # fresh DB will be created from models with correct defaults

    if not _column_exists(inspector, "devices", "polling_interval_seconds"):
        op.add_column(
            "devices",
            sa.Column("polling_interval_seconds", sa.Integer(), nullable=True),
        )

    # Change server default for NEW rows only (existing rows untouched).
    conn.exec_driver_sql(
        "ALTER TABLE devices ALTER COLUMN monitoring_enabled SET DEFAULT false"
    )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "devices" not in inspector.get_table_names():
        return

    conn.exec_driver_sql(
        "ALTER TABLE devices ALTER COLUMN monitoring_enabled SET DEFAULT true"
    )
    if _column_exists(inspector, "devices", "polling_interval_seconds"):
        op.drop_column("devices", "polling_interval_seconds")
