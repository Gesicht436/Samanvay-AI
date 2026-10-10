"""Regenerate backend/alembic/baseline_schema.py from the current ORM metadata.

This is a MAINTENANCE tool, not part of normal operation.  Run it ONLY when the
schema genuinely changes, and pair it with a NEW migration revision — never edit
the generated file by hand.  The generated module is the frozen snapshot that
existing-database adoption and startup verification compare against.

Usage (from the repository root):
    python scripts/generate_baseline_schema.py

It performs no database access; it compiles ``Base.metadata`` against the
PostgreSQL dialect and writes the resulting DDL statements to
backend/alembic/baseline_schema.py.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.schema import CreateIndex, CreateTable  # noqa: E402
from sqlalchemy.dialects import postgresql  # noqa: E402

import backend.app.models.tables  # noqa: F401,E402
from backend.app.models.base import Base  # noqa: E402

OUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "backend", "alembic", "baseline_schema.py"
)


def build_statements() -> list[str]:
    dialect = postgresql.dialect()
    stmts: list[str] = []
    for table in Base.metadata.sorted_tables:
        stmts.append(str(CreateTable(table).compile(dialect=dialect)).strip().rstrip(";"))
    for table in Base.metadata.sorted_tables:
        for idx in sorted(table.indexes, key=lambda i: i.name):
            stmts.append(
                str(CreateIndex(idx).compile(dialect=dialect)).strip().rstrip(";")
            )
    return stmts


def build_tables_reverse() -> list[str]:
    return [t.name for t in reversed(list(Base.metadata.sorted_tables))]


def main() -> int:
    stmts = build_statements()
    tables = build_tables_reverse()

    header = '''"""Frozen baseline schema for migration 0001.

This module is the single source of truth for the *expected* current schema
during existing-database adoption and startup verification.  It is derived
mechanically from ``backend.app.models.tables`` compiled against the
PostgreSQL dialect, then frozen here so that adoption compares a live
database against a fixed snapshot rather than against the (mutable) ORM
metadata.

Regenerate ONLY via ``scripts/generate_baseline_schema.py`` when the schema
genuinely changes, and pair the regeneration with a new migration revision.
Do not hand-edit the statements below.
"""

BASELINE_STATEMENTS = [
'''

    body = ",\n".join(f"    {s!r}" for s in stmts)
    footer = f''']

# The single revision this baseline represents.  Adoption stamps exactly this
# value into alembic_version, and startup verification requires exactly this
# value, so both paths agree with versions/0001_baseline.py by construction.
BASELINE_REVISION = "0001"

# Table names in reverse-dependency (teardown-safe) order, used by the
# baseline downgrade.  Derived from the same dependency ordering SQLAlchemy uses.
BASELINE_TABLES = {tables!r}
'''

    content = header + body + "\n" + footer
    with open(os.path.abspath(OUT_PATH), "w", encoding="utf-8") as f:
        f.write(content)

    print(
        f"[GEN] Wrote {len(stmts)} statements / {len(tables)} tables to "
        f"{os.path.abspath(OUT_PATH)}"
    )
    print("[GEN] Remember to add a NEW migration revision; do not edit 0001 in place.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
