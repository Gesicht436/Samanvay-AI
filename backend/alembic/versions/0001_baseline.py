"""0001 baseline: create the full 12-table Samanvay-AI schema.

Reproduces exactly what Base.metadata already produces, so a fresh database
can be provisioned from versioned migrations instead of create_all(). This
baseline introduces no new authentication architecture; it snapshots the
existing ORM schema (users, auth_sessions, security_events and the business
tables). Statements are the frozen DDL in backend/alembic/baseline_schema.py.

Existing databases initialized via create_all() must NOT run this upgrade;
adopt them with scripts/adopt_schema.py (stamp only after verification).
"""

from __future__ import annotations

from alembic import op

from backend.alembic.baseline_schema import BASELINE_STATEMENTS, BASELINE_TABLES, BASELINE_REVISION

# revision identifiers, used by Alembic.
revision = BASELINE_REVISION
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    for stmt in BASELINE_STATEMENTS:
        op.execute(stmt)


def downgrade() -> None:
    # Reverse dependency order for safe teardown.
    for table in BASELINE_TABLES:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
