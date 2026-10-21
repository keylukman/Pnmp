"""metrics null semantics: remove fabricated zero defaults, widen counters

Step 8.3: rx/tx counters, rates and utilization columns on device_interfaces
and interface_metrics previously carried client-side ``default=0`` which made
SQLAlchemy fabricate zeros for unavailable data (first-poll rates, missing
counters). They are now nullable with no default; raw byte/error/discards
counters are widened to BigInteger (64-bit SNMP counters exceed INT32).

No server_default existed on these columns in PostgreSQL, so this migration
only documents the intent and is fully reversible. Existing rows are
untouched: historical zeros remain valid measurements.
"""
import sqlalchemy as sa
from alembic import op

revision = "20261012_0002"
down_revision = "20261009_0001"
branch_labels = None
depends_on = None

COUNTER_COLS = ["rx_bytes", "tx_bytes", "rx_errors", "tx_errors", "rx_discards", "tx_discards"]
RATE_COLS = ["rx_bps", "tx_bps"]
UTIL_COLS = ["utilization_in", "utilization_out"]
TABLES = ["device_interfaces", "interface_metrics"]


def _pg_type(table, col):
    return "BIGINT" if col in COUNTER_COLS else "INTEGER"


def upgrade():
    conn = op.get_bind()
    for table in TABLES:
        for col in COUNTER_COLS + RATE_COLS + UTIL_COLS:
            conn.execute(sa.text(
                f'ALTER TABLE {table} ALTER COLUMN {col} DROP DEFAULT'
            ))
            conn.execute(sa.text(
                f'ALTER TABLE {table} ALTER COLUMN {col} TYPE {_pg_type(table, col)} USING {col}::{_pg_type(table, col)}'
            ))
    # device_interfaces.utilization (current-state mirror)
    conn.execute(sa.text('ALTER TABLE device_interfaces ALTER COLUMN utilization DROP DEFAULT'))
    conn.execute(sa.text('ALTER TABLE device_interfaces ALTER COLUMN utilization TYPE INTEGER USING utilization::INTEGER'))


def downgrade():
    # Types revert; defaults were client-side only (never server-side), so
    # there is nothing to restore at the database level. Re-adding fabricated
    # client defaults would be a code change, not a schema change.
    conn = op.get_bind()
    for table in TABLES:
        for col in COUNTER_COLS:
            conn.execute(sa.text(
                f'ALTER TABLE {table} ALTER COLUMN {col} TYPE INTEGER USING {col}::INTEGER'
            ))
