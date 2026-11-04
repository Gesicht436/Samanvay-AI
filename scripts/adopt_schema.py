"""Explicit, operator-invoked adoption of an existing create_all() database.

This script NEVER creates, alters, or drops schema.  It only ever *reads* the
live catalog and compares it against the frozen baseline
(``backend.alembic.baseline_schema``).  On an exact match and an explicit
``--stamp``, it inserts the baseline revision into the ``alembic_version``
table — the same single-row write that ``alembic stamp head`` performs — so the
database becomes migration-managed without any DDL ever running.

Safety contract:
  * Default behaviour is DRY-RUN (no writes).  Stamping requires ``--stamp``.
  * Any schema difference, missing object, or unverifiable object aborts with a
    non-zero exit and makes NO write.
  * Adoption compares the frozen baseline, not the current ORM metadata, so it
    reflects the schema the migration would have produced.
  * No rows, data, or existing tables are changed — only one new row in
    ``alembic_version`` may be inserted.
  * Partial-index predicates are read from the ``pg_indexes`` catalog with a
    read-only SELECT and passed to the comparison; an index definition whose
    predicate cannot be extracted aborts verification (fail closed, no write).

Usage (run from the repository root):
    python scripts/adopt_schema.py            # dry-run report only
    python scripts/adopt_schema.py --stamp    # verify then stamp (one insert)
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import inspect, text  # noqa: E402

from backend.app.core.config import settings  # noqa: E402
from backend.app.models.base import engine  # noqa: E402
from backend.alembic.baseline_schema import BASELINE_REVISION  # noqa: E402
from backend.app.services.schema_verification import (  # noqa: E402
    _balanced,
    actual_from_inspector,
    check_tokens,
    compare_snapshots,
    expected_from_baseline,
)

EXPECTED_TABLES_OWNED = {"alembic_version"}


def _alembic_version_rows() -> list[str]:
    with engine.connect() as conn:
        insp = inspect(conn)
        if not insp.has_table("alembic_version"):
            return []
        return [row[0] for row in conn.execute(text("SELECT version_num FROM alembic_version"))]


def _print_report(diffs: list[str]) -> None:
    if not diffs:
        print("[ADOPT] Live schema matches the frozen baseline exactly.")
        return
    print(f"[ADOPT] MISMATCH — {len(diffs)} difference(s) detected:")
    for d in diffs:
        print(f"    - {d}")


def predicate_from_indexdef(indexdef: str) -> str | None:
    """Extract the partial-index WHERE predicate from a pg_get_indexdef() definition.

    Returns ``None`` when the definition positively contains no WHERE clause
    (an ordinary non-partial index — a verified fact, not an unknown).  Raises
    ``ValueError`` when a WHERE clause is present but cannot be extracted and
    balanced, so callers abort instead of treating an unverified predicate as
    a match.

    The match anchors on the ``) WHERE`` that closes the index column list;
    CREATE INDEX column expressions cannot contain a top-level WHERE, so the
    first such occurrence is the partial-index predicate.
    """
    m = re.search(r"\)\s*WHERE\s*(.*)$", indexdef or "", re.DOTALL)
    if not m:
        return None
    pred = (m.group(1) or "").strip()
    if not pred:
        raise ValueError(f"unparseable index predicate (empty WHERE clause): {indexdef!r}")
    # check_tokens strips redundant balanced outer parentheses and normalizes
    # casing/whitespace the same way the baseline side is normalized.
    pred = " ".join(check_tokens(pred))
    if not pred or not _balanced(pred):
        raise ValueError(f"unparseable index predicate: {indexdef!r}")
    return pred


def _index_predicates(conn) -> dict:
    """Read-only catalog query: table -> {index_name: predicate}.

    ``predicate`` is ``None`` for a positively non-partial index.  Any
    unparseable definition raises, which aborts verification (fail closed).
    """
    rows = conn.execute(
        text(
            "SELECT tablename, indexname, indexdef FROM pg_indexes "
            "WHERE schemaname = current_schema()"
        )
    ).fetchall()
    out: dict = {}
    for tablename, indexname, indexdef in rows:
        out.setdefault(str(tablename), {})[str(indexname)] = predicate_from_indexdef(
            str(indexdef)
        )
    return out


def _verify() -> list[str]:
    """Read-only comparison of the live catalog against the frozen baseline."""
    expected = expected_from_baseline()
    with engine.connect() as conn:
        predicates = _index_predicates(conn)
        actual = actual_from_inspector(inspect(conn), index_predicates=predicates)
    return compare_snapshots(expected, actual)


def _stamp() -> None:
    """Insert the baseline revision into alembic_version (idempotent)."""
    existing = _alembic_version_rows()
    if BASELINE_REVISION in existing:
        print(f"[ADOPT] Already stamped at {BASELINE_REVISION}; nothing to do.")
        return
    with engine.begin() as conn:
        insp = inspect(conn)
        if not insp.has_table("alembic_version"):
            conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL, CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"))
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES (:v)"), {"v": BASELINE_REVISION})
    print(f"[ADOPT] Stamped {BASELINE_REVISION} (schema is now migration-managed).")


def main(argv: list[str]) -> int:
    stamp = "--stamp" in argv
    if argv and not all(a == "--stamp" for a in argv):
        print(f"[ADOPT] Unknown argument(s): {argv}", file=sys.stderr)
        return 2

    print(f"[ADOPT] Target DB: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")
    print("[ADOPT] Mode:", "STAMP (verify then adopt)" if stamp else "DRY-RUN (no writes)")

    try:
        diffs = _verify()
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"[ADOPT] ABORT — could not verify schema: {exc}", file=sys.stderr)
        return 3

    _print_report(diffs)

    if diffs:
        print("[ADOPT] ABORT — schema does not match the baseline; NOT stamping.", file=sys.stderr)
        print("[ADOPT] Resolve the differences above before adoption. No changes were made.")
        return 1

    if not stamp:
        print("[ADOPT] Dry-run complete. Re-run with --stamp to adopt (one insert).")
        return 0

    _stamp()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
