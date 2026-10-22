"""sync devices table with current ORM model (monitoring columns)

Milestone 1 finalization. Root cause of the runtime error:

    psycopg.errors.UndefinedColumn: column devices.monitoring_method does not exist

The user's PostgreSQL ``devices`` table was created by an OLD copy of
``Base.metadata.create_all`` (before the monitoring columns existed in the
Device model). create_all never ALTERs existing tables, so the new ORM columns
were missing and the scheduler SELECT failed every loop.

This migration is IDEMPOTENT and NON-DESTRUCTIVE: it inspects the live schema
and adds ONLY the missing devices columns, matching app/models/models.py:

  * monitoring_method          SQLEnum(MonitoringMethod) -> native PG enum
                                 'monitoringmethod' if absent, else VARCHAR
  * polling_interval_seconds   INTEGER NULL
  * failure_count              INTEGER NOT NULL DEFAULT 0
  * is_demo                    BOOLEAN NOT NULL DEFAULT false

Existing rows are backfilled with defaults consistent with the Phase 3 Step 8
policy (monitoring stays OFF until an administrator enables it per device).
No column or row is ever dropped or modified beyond ADD COLUMN + defaults.
Safe on fresh databases (no-op) and on already-synced databases (no-op).
"""
import sqlalchemy as sa
from alembic import op

revision = "20261022_0003"
down_revision = "20261012_0002"
branch_labels = None
depends_on = None


def _pg_enum_exists(conn, name: str) -> bool:
    try:
        return conn.execute(
            sa.text("SELECT 1 FROM pg_type WHERE typname = :n"), {"n": name}
        ).scalar() is not None
    except Exception:
        return False


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "devices" not in inspector.get_table_names():
        return  # fresh DB will be created from models with correct columns

    existing = {c["name"] for c in inspector.get_columns("devices")}

    # --- monitoring_method -------------------------------------------------
    if "monitoring_method" not in existing:
        if _pg_enum_exists(conn, "monitoringmethod"):
            conn.execute(sa.text(
                "ALTER TABLE devices ADD COLUMN monitoring_method "
                "monitoringmethod NOT NULL DEFAULT 'NONE'"
            ))
        else:
            # create_all would have created the enum; if it doesn't exist we
            # still must not fabricate types the ORM can't read. SQLAlchemy's
            # SQLEnum stores member NAMES as text, so a VARCHAR column is
            # compatible for reads/writes.
            conn.execute(sa.text(
                "ALTER TABLE devices ADD COLUMN monitoring_method "
                "VARCHAR NOT NULL DEFAULT 'NONE'"
            ))

    # --- polling_interval_seconds -----------------------------------------
    if "polling_interval_seconds" not in existing:
        conn.execute(sa.text(
            "ALTER TABLE devices ADD COLUMN polling_interval_seconds INTEGER NULL"
        ))

    # --- failure_count -----------------------------------------------------
    if "failure_count" not in existing:
        conn.execute(sa.text(
            "ALTER TABLE devices ADD COLUMN failure_count INTEGER NOT NULL DEFAULT 0"
        ))

    # --- is_demo -----------------------------------------------------------
    if "is_demo" not in existing:
        conn.execute(sa.text(
            "ALTER TABLE devices ADD COLUMN is_demo BOOLEAN NOT NULL DEFAULT false"
        ))


def downgrade() -> None:
    # Intentionally minimal: these columns are required by the current ORM and
    # scheduler. Dropping them would re-break the application, so downgrade is
    # a documented no-op rather than a destructive DROP COLUMN.
    pass
