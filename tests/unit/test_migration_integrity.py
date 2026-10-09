"""Database-free integrity tests for the Task 20 migration infrastructure.

These tests never touch PostgreSQL.  They verify, without a live database:

1. Migration-chain integrity: exactly one head, the baseline parses, and its
   `down_revision` is `None`.
2. Baseline fidelity: the frozen baseline statements render exactly the schema
   the application expects (tables, columns/types, nullability, primary and
   foreign keys, ON DELETE deletion behaviour, unique constraints, server
   defaults, generated columns, and indexes -- including the partial
   active-session index).  Every expected fact is hand-authored from the frozen
   DDL in `backend/alembic/baseline_schema.py`; it is never rebuilt from ORM
   metadata at test time, so the frozen snapshot is validated against
   independently written expectations rather than by comparing two fresh views
   of the same mutable ORM metadata.
3. Adoption fail-closed / no-write behaviour: a mismatched or unverifiable
   catalog aborts without stamping; only an exact match can stamp.
4. Production startup verification: missing version state, revision mismatch,
   and missing required tables all raise (fails closed) via mocked
   connections -- never a real one.
5. Migration-chain statement / teardown coverage is retained and extended.
6. Baseline drift detection: regenerating the frozen baseline from the
   authoritative ORM metadata must be byte-identical, and Alembic's own
   ScriptDirectory must report exactly one head (both offline, no database).
7. Index-predicate verification: partial-index predicates are extracted from
   read-only pg_indexes definitions over fake connections; a matching
   predicate verifies, while mismatched, missing, or unparseable predicates
   stay fail-closed with zero writes.

They do NOT prove live PostgreSQL behaviour (index runtime existence, FK
enforcement, server-default application, data preservation); those remain
blocked until PostgreSQL is available and are called out explicitly.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from unittest import mock
from unittest.mock import patch

from backend.app.models.base import Base, verify_schema_version
from backend.app.services.schema_verification import (
    ColumnFacts,
    IndexFacts,
    SchemaSnapshot,
    UNVERIFIABLE,
    actual_from_inspector,
    compare_snapshots,
    expected_from_baseline,
)
from backend.alembic.baseline_schema import (
    BASELINE_REVISION,
    BASELINE_STATEMENTS,
    BASELINE_TABLES,
)
from scripts.generate_baseline_schema import build_statements, build_tables_reverse

# ── Frozen, hand-authored expectations from the baseline DDL ───────────────
EXPECTED_TABLES = frozenset(
    {
        "active_learning_feedback",
        "cdc_outbox",
        "idempotency_keys",
        "ingested_documents",
        "sovereign_audit_ledger",
        "users",
        "auth_sessions",
        "inventory_items",
        "requisitions",
        "security_events",
        "digital_gate_passes",
        "inventory_locks",
    }
)

EXPECTED_PRIMARY_KEYS = {
    "active_learning_feedback": ("id",),
    "cdc_outbox": ("id",),
    "idempotency_keys": ("key",),
    "ingested_documents": ("id",),
    "sovereign_audit_ledger": ("log_id",),
    "users": ("id",),
    "auth_sessions": ("id",),
    "inventory_items": ("id",),
    "requisitions": ("requisition_id",),
    "security_events": ("id",),
    "digital_gate_passes": ("gate_pass_no",),
    "inventory_locks": ("id",),
}

EXPECTED_FOREIGN_KEYS = {
    "active_learning_feedback": (),
    "cdc_outbox": (),
    "idempotency_keys": (),
    "ingested_documents": (),
    "sovereign_audit_ledger": (),
    "users": (),
    "auth_sessions": (("user_id", "users", "id", "CASCADE"),),
    "inventory_items": (("source_document_id", "ingested_documents", "id", None),),
    "requisitions": (("sku_code", "inventory_items", "sku_code", None),),
    "security_events": (
        ("user_id", "users", "id", "SET NULL"),
        ("session_id", "auth_sessions", "id", "SET NULL"),
    ),
    "digital_gate_passes": (("requisition_id", "requisitions", "requisition_id", None),),
    "inventory_locks": (
        ("sku_code", "inventory_items", "sku_code", None),
        ("requisition_id", "requisitions", "requisition_id", None),
    ),
}



EXPECTED_UNIQUE_CONSTRAINTS = {
    "active_learning_feedback": (),
    "cdc_outbox": (),
    "idempotency_keys": (),
    "ingested_documents": (),
    "sovereign_audit_ledger": (),
    "users": (("email",),),
    "auth_sessions": (),
    "inventory_items": (),
    "requisitions": (),
    "security_events": (),
    "digital_gate_passes": (),
    "inventory_locks": (),
}

EXPECTED_DEFAULTS = {"users": {"is_active": "true", "is_approved": "false"}}

EXPECTED_GENERATED_COLUMNS = {
    "active_learning_feedback": (),
    "cdc_outbox": (),
    "idempotency_keys": (),
    "ingested_documents": (),
    "sovereign_audit_ledger": (),
    "users": (),
    "auth_sessions": (),
    "inventory_items": ("total_value_inr",),
    "requisitions": (),
    "security_events": (),
    "digital_gate_passes": (),
    "inventory_locks": (),
}

EXPECTED_CHECK_CONSTRAINTS = {
    "active_learning_feedback": (),
    "cdc_outbox": (),
    "idempotency_keys": (),
    "ingested_documents": (),
    "sovereign_audit_ledger": (),
    "users": (),
    "auth_sessions": (),
    "inventory_items": (("QUANTITY", ">=", "0"),),
    "requisitions": (("REQUIRED_QTY", ">", "0"),),
    "security_events": (),
    "digital_gate_passes": (),
    "inventory_locks": (("LOCKED_QTY", ">", "0"),),
}



EXPECTED_PARTIAL_INDEX = {
    "auth_sessions": {
        "ix_auth_sessions_user_expires_active": IndexFacts(
            columns=("user_id", "expires_at"),
            unique=False,
            predicate="REVOKED_AT IS NULL",
        ),
        "ix_auth_sessions_session_token_hash": IndexFacts(
            columns=("session_token_hash",), unique=True, predicate=None
        ),
    }
}

EXPECTED_INDEX_COUNT = 23

# ── Fake engines / inspectors (no database touched) ────────────────────────


def _fake_engine(rows=None):
    """A fully controllable SQLAlchemy-engine twin for `verify_schema_version`.

    `rows` is the list of `("version_num",)` tuples the fake `alembic_version`
    table yields.  The fake never connects to a database.
    """
    rows = list(rows) if rows is not None else [("0001",)]
    conn = mock.MagicMock()
    conn.execute.return_value.fetchall.return_value = rows
    manager = mock.MagicMock()
    manager.__enter__.return_value = conn
    manager.__exit__.return_value = False
    engine = mock.MagicMock()
    engine.connect.return_value = manager
    return engine


def _patch_inspect(has_version=True, table_names=None):
    """Temporarily make `sqlalchemy.inspect(conn)` yield a scripted inspector."""
    insp = mock.MagicMock()
    insp.has_table.return_value = has_version
    if table_names is not None:
        insp.get_table_names.return_value = set(table_names)
    else:
        insp.get_table_names.return_value = set(BASELINE_TABLES)
    # Make the mock return itself when called (so inspect(conn) returns the same mock)
    insp.return_value = insp
    return mock.patch("sqlalchemy.inspect", new=insp)

# ── 1. Migration chain & statement coverage ────────────────────────────────


def _revision_metadata():
    """Parse the 0001 migration's revision identifiers via AST.

    Alembic is an optional dependency in the DB-free environment, and the
    migration module performs `from alembic import op` at import time.  We
    therefore read the module-level `revision`/`down_revision` assignments
    statically, so chain-integrity tests never import alembic or touch a DB.
    """
    import ast
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[2]
        / "backend"
        / "alembic"
        / "versions"
        / "0001_baseline.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in {
                "revision",
                "down_revision",
                "depends_on",
                "branch_labels",
            }:
                try:
                    found[target.id] = ast.literal_eval(node.value)
                except ValueError:
                    found[target.id] = getattr(node.value, "id", None)
    return found


def test_baseline_revision_is_single_head_with_no_parent():
    meta = _revision_metadata()
    assert meta["revision"] in ("0001", "BASELINE_REVISION")
    assert BASELINE_REVISION == "0001"
    assert meta["down_revision"] is None
    assert meta["depends_on"] is None
    assert meta["branch_labels"] is None


def test_baseline_revision_matches_frozen_schema_revision():
    meta = _revision_metadata()
    assert meta["revision"] in (BASELINE_REVISION, "BASELINE_REVISION")


def test_baseline_revision_chain_is_frozen():
    # The versioned migration must bind `revision` to the frozen
    # BASELINE_REVISION constant and carry no parent, no depends_on, and no
    # branch label.  Adoption stamps and startup verification both rely on it.
    meta = _revision_metadata()
    assert meta["revision"] in (BASELINE_REVISION, "BASELINE_REVISION")
    assert meta["down_revision"] is None
    assert meta["depends_on"] is None
    assert meta["branch_labels"] is None


def test_baseline_statement_set_covers_all_twelve_tables():
    assert len(BASELINE_TABLES) == 12
    expected = expected_from_baseline()
    assert set(expected.tables) == set(BASELINE_TABLES)
    creates = [
        s for s in BASELINE_STATEMENTS if s.strip().upper().startswith("CREATE TABLE")
    ]
    assert len(creates) == 12


def test_baseline_statement_set_covers_object_shapes():
    # Every baseline statement is a CREATE TABLE or a CREATE INDEX, and every
    # CREATE TABLE parses into a table entry.  No stray DDL.
    creates = [
        s for s in BASELINE_STATEMENTS if s.strip().upper().startswith("CREATE TABLE")
    ]
    index_stmts = [
        s
        for s in BASELINE_STATEMENTS
        if s.strip().upper().startswith(("CREATE INDEX", "CREATE UNIQUE INDEX"))
    ]
    assert len(creates) == 12
    assert len(index_stmts) == EXPECTED_INDEX_COUNT
    for stmt in BASELINE_STATEMENTS:
        head = stmt.strip().upper()
        assert (
            head.startswith(("CREATE TABLE", "CREATE INDEX", "CREATE UNIQUE INDEX"))
        ), f"unexpected baseline statement {stmt[:60]!r}"


def test_baseline_downgrade_teardown_order_is_reverse_dependency():
    order = {t: i for i, t in enumerate(BASELINE_TABLES)}
    assert order["security_events"] < order["auth_sessions"] < order["users"]

# ── 2. Frozen baseline fidelity ────────────────────────────────────────────


def test_baseline_tableset_matches_hand_audited_frozen_schema():
    # Hand-authored set comes from the frozen DDL, never ORM metadata at test
    # time.  A mismatch means the frozen baseline was edited without
    # regenerating the migration or the verification tables.
    assert set(expected_from_baseline().tables) == EXPECTED_TABLES
    assert set(BASELINE_TABLES) == EXPECTED_TABLES


def test_baseline_primary_keys_are_hand_audited():
    snap = expected_from_baseline()
    assert snap.primary_keys == EXPECTED_PRIMARY_KEYS


def test_baseline_foreign_key_actions_are_hand_audited():
    # ON DELETE behaviour encoded in the frozen DDL: auth_sessions cascades
    # from users, security_events rows become NULL, business tables carry no
    # ON DELETE clause (ownership relationships stay consistent).
    snap = expected_from_baseline()
    assert snap.foreign_keys == EXPECTED_FOREIGN_KEYS


def test_baseline_unique_constraints_are_hand_audited():
    snap = expected_from_baseline()
    assert snap.uniques == EXPECTED_UNIQUE_CONSTRAINTS
    assert snap.tables["users"]["email"].nullable is True


def test_baseline_server_defaults_are_hand_audited():
    snap = expected_from_baseline()
    assert snap.tables["users"]["is_active"].type == "BOOLEAN"
    assert snap.tables["users"]["is_active"].server_default == "true"
    assert snap.tables["users"]["is_active"].nullable is False
    assert snap.tables["users"]["is_approved"].server_default == "false"
    assert snap.tables["users"]["email"].nullable is True


def test_baseline_generated_column_is_hand_audited():
    snap = expected_from_baseline()
    assert EXPECTED_GENERATED_COLUMNS == snap.generated_columns
    facts = snap.tables["inventory_items"]["total_value_inr"]
    assert facts.type == "NUMERIC(14, 2)"


def test_baseline_check_constraints_are_hand_audited():
    snap = expected_from_baseline()
    assert snap.checks == EXPECTED_CHECK_CONSTRAINTS


def test_baseline_partial_index_is_hand_audited():
    snap = expected_from_baseline()
    ix = snap.indexes["auth_sessions"]["ix_auth_sessions_user_expires_active"]
    assert ix.unique is False
    assert ix.columns == ("user_id", "expires_at")
    assert ix.predicate == "REVOKED_AT IS NULL"
    assert snap.indexes["auth_sessions"]["ix_auth_sessions_session_token_hash"].predicate is None
    assert sum(len(v) for v in snap.indexes.values()) == EXPECTED_INDEX_COUNT


def test_baseline_index_tables_are_hand_audited():
    snap = expected_from_baseline()
    assert set(snap.indexes) == {
        "active_learning_feedback",
        "cdc_outbox",
        "users",
        "auth_sessions",
        "inventory_items",
        "security_events",
        "sovereign_audit_ledger",
        "inventory_locks",
        "ingested_documents",
        "digital_gate_passes",
        "idempotency_keys",
        "requisitions",
    }

# ── 3. Production startup verification (fails closed) ──────────────────────

BASE_TABLE_NAMES = set(BASELINE_TABLES)


def test_verify_missing_alembic_version_fails_closed():
    with _patch_inspect(has_version=False):
        with pytest.raises(RuntimeError, match="alembic_version"):
            verify_schema_version(engine_obj=_fake_engine())


def test_verify_zero_rows_revision_fails_closed():
    with _patch_inspect():
        with pytest.raises(RuntimeError, match="recorded revision"):
            verify_schema_version(engine_obj=_fake_engine(rows=[]))


def test_verify_revision_mismatch_fails_closed():
    with _patch_inspect():
        with pytest.raises(RuntimeError, match="recorded revision"):
            verify_schema_version(engine_obj=_fake_engine(rows=[("9999",)]))


def test_verify_ambiguous_revision_fails_closed():
    # Two distinct recorded revisions are not a single head; fail closed.
    with _patch_inspect():
        with pytest.raises(RuntimeError, match="recorded revision"):
            verify_schema_version(engine_obj=_fake_engine(rows=[("0001",), ("0002",)]))


def test_verify_missing_required_table_fails_closed():
    missing = "sovereign_audit_ledger"
    present = BASE_TABLE_NAMES - {missing}
    with _patch_inspect(table_names=present):
        conn = _fake_engine()
        conn.execute.return_value.fetchall.return_value = [("0001",)]
        with pytest.raises(RuntimeError, match="missing required table"):
            verify_schema_version(engine_obj=conn, required_tables=BASE_TABLE_NAMES)


def test_verify_successful_expected_revision_passes():
    with _patch_inspect():
        verify_schema_version(engine_obj=_fake_engine(), expected_revision=BASELINE_REVISION)


def test_verify_inspection_error_fails_closed():
    # A failure while reading the catalog (connect/inspect failure) must abort
    # rather than report success.
    with _patch_inspect():
        engine = _fake_engine()
        engine.connect.side_effect = RuntimeError("inspection failed")
        with pytest.raises(Exception):
            verify_schema_version(engine_obj=engine)

# ── 4. Adoption safety (no writes; fail-closed) ────────────────────────────


def _load_adopt_schema():
    """Import `scripts/adopt_schema.py` without polluting `sys.path`."""
    import importlib.util

    path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "adopt_schema.py")
    spec = importlib.util.spec_from_file_location("adopt_schema", path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["adopt_schema"] = module
    spec.loader.exec_module(module)
    return module


_adopt = _load_adopt_schema()
main = _adopt.main


class _FakeResult:
    """Minimal SQLAlchemy Result twin: supports fetchall() and iteration."""

    def __init__(self, rows):
        self._rows = list(rows)

    def fetchall(self):
        return list(self._rows)

    def __iter__(self):
        return iter(self._rows)


_WRITE_PREFIXES = frozenset({
    "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "TRUNCATE",
    "GRANT", "REVOKE", "COMMENT", "RENAME", "VACUUM", "CALL", "DO",
})


def _assert_no_writes(conn_mock):
    """Fail if any statement executed on this connection is a write or DDL."""
    for call in conn_mock.execute.call_args_list:
        stmt = str(call.args[0]) if call.args else ""
        first = stmt.lstrip().split(None, 1)[0].upper() if stmt.strip() else ""
        assert first not in _WRITE_PREFIXES, f"write attempted in read-only path: {stmt!r}"


def _adopt_engine(rows=None, pg_rows=None):
    """A fake engine twin for `scripts/adopt_schema.py`.

    The inner read connection dispatches by statement: the read-only
    pg_indexes predicate query yields `pg_rows`, the alembic_version
    pre-check yields `rows`, and any other statement fails loudly.
    `engine.begin()` yields a separate write connection for stamp assertions.
    """
    rows = list(rows) if rows is not None else [("0001",)]
    pg_rows = list(pg_rows) if pg_rows is not None else []
    conn = mock.MagicMock()

    def _execute(stmt, *args, **kwargs):
        s = str(stmt)
        if "pg_indexes" in s:
            return _FakeResult(pg_rows)
        if "version_num" in s:
            return _FakeResult(rows)
        raise AssertionError(f"unexpected statement on read connection: {s!r}")

    conn.execute.side_effect = _execute
    manager = mock.MagicMock()
    manager.__enter__.return_value = conn
    manager.__exit__.return_value = False
    engine = mock.MagicMock()
    engine.connect.return_value = manager
    engine.begin.return_value.__enter__.return_value = mock.MagicMock()
    return engine


def _pg_conn(pg_rows):
    """A fake connection whose only job is answering the pg_indexes query."""
    conn = mock.MagicMock()

    def _execute(stmt, *args, **kwargs):
        assert "pg_indexes" in str(stmt), f"unexpected statement: {stmt}"
        return _FakeResult(pg_rows)

    conn.execute.side_effect = _execute
    return conn


def _adopt_inspector():
    insp = mock.MagicMock()
    insp.has_table.return_value = True
    insp.get_table_names.return_value = set(BASELINE_TABLES)
    # patch(..., new=insp) calls the mock; make it return itself so
    # inspect(conn) yields the scripted inspector.
    insp.return_value = insp
    return insp


def test_adopt_dry_run_exact_match_no_write():
    # Dry-run performs only read statements (the pg_indexes predicate query);
    # stamping is an explicit --stamp choice. Any write on either connection
    # fails this test.
    engine = _adopt_engine()
    read_conn = engine.connect.return_value.__enter__.return_value
    with patch("adopt_schema.inspect", new=_adopt_inspector()), \
         patch("adopt_schema.engine", engine), \
         patch("adopt_schema.actual_from_inspector", return_value=expected_from_baseline()):
        rc = main([])
        assert rc == 0
        engine.connect.assert_called_once()
        engine.begin.assert_not_called()
        _assert_no_writes(read_conn)


def test_adopt_mismatch_aborts_no_write():
    # Mutate the captured actual snapshot to force one real difference.
    snap = expected_from_baseline()
    del snap.tables["users"]
    engine = _adopt_engine()
    read_conn = engine.connect.return_value.__enter__.return_value
    with patch("adopt_schema.inspect", new=_adopt_inspector()), \
         patch("adopt_schema.engine", engine), \
         patch("adopt_schema.actual_from_inspector", return_value=snap):
        rc = main([])
        assert rc == 1
        engine.connect.assert_called_once()
        engine.begin.assert_not_called()
        _assert_no_writes(read_conn)


def test_adopt_unverifiable_index_aborts_without_stamp():
    snap = expected_from_baseline()
    snap.indexes["auth_sessions"]["ix_auth_sessions_user_expires_active"] = IndexFacts(
        columns=("user_id", "expires_at"), unique=True, predicate=UNVERIFIABLE
    )
    engine = _adopt_engine()
    read_conn = engine.connect.return_value.__enter__.return_value
    with patch("adopt_schema.inspect", new=_adopt_inspector()), \
         patch("adopt_schema.engine", engine), \
         patch("adopt_schema.actual_from_inspector", return_value=snap):
        rc = main(["--stamp"])
        assert rc == 1
        engine.connect.assert_called_once()
        engine.begin.assert_not_called()
        _assert_no_writes(read_conn)


def test_adopt_stamp_only_after_successful_comparison():
    # alembic_version is absent; on a clean match, stamping must proceed
    # with exactly one write (the version insert) and only after the
    # comparison passed. Two read-only connects happen first: _verify() and
    # the stamp pre-check.
    engine = _adopt_engine(rows=[])
    with patch("adopt_schema.inspect", new=_adopt_inspector()), \
         patch("adopt_schema.engine", engine), \
         patch("adopt_schema.actual_from_inspector", return_value=expected_from_baseline()):
        rc = main(["--stamp"])
        assert rc == 0
        assert engine.connect.call_count == 2
        engine.begin.assert_called_once()
        begin_conn = engine.begin.return_value.__enter__.return_value
        writes = [str(c.args[0]) for c in begin_conn.execute.call_args_list]
        assert len(writes) == 1
        assert writes[0].upper().startswith("INSERT INTO ALEMBIC_VERSION")


def test_adopt_already_stamped_is_idempotent():
    engine = _adopt_engine(rows=[("0001",)])
    read_conn = engine.connect.return_value.__enter__.return_value
    with patch("adopt_schema.inspect", new=_adopt_inspector()), \
         patch("adopt_schema.engine", engine), \
         patch("adopt_schema.actual_from_inspector", return_value=expected_from_baseline()):
        rc = main(["--stamp"])
        assert rc == 0
        # Two read-only connects (verify + pre-check); the pre-check finds the
        # stamp already present, so no write may occur.
        assert engine.connect.call_count == 2
        engine.begin.assert_not_called()
        _assert_no_writes(read_conn)


def test_adopt_unknown_arg_rejected_before_verify():
    rc = main(["--bogus"])
    assert rc == 2


# ── 5. Baseline ↔ ORM drift and offline single head ──────────────────────


def test_frozen_baseline_matches_orm_metadata_regeneration():
    # The frozen baseline must stay byte-identical to a fresh regeneration
    # from the authoritative ORM metadata. Drift means either a hand-edited
    # baseline or an ORM change without regeneration + a new migration. The
    # hand-authored EXPECTED_* tables above remain the independent check that
    # the frozen baseline itself encodes the correct schema.
    assert build_statements() == list(BASELINE_STATEMENTS)
    assert build_tables_reverse() == list(BASELINE_TABLES)


def test_alembic_script_directory_reports_single_head():
    # Offline validation through Alembic's own script directory (no env.py
    # execution, no database): exactly one head, equal to the baseline
    # revision, and exactly one revision in the chain.
    pytest.importorskip("alembic")
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    root = Path(__file__).resolve().parents[2]
    cfg = Config(str(root / "backend" / "alembic.ini"))
    cfg.set_main_option("script_location", (root / "backend" / "alembic").as_posix())
    sd = ScriptDirectory.from_config(cfg)
    assert sd.get_heads() == [BASELINE_REVISION]
    assert len(list(sd.walk_revisions())) == 1


# ── 6. Index-predicate verification (fake connections; no database) ──────
#
# Representative pg_get_indexdef() output for the two auth_sessions indexes.
# Note: a reflected PG column type renders through str() as bare 'TIMESTAMP'
# for both tz and naive spellings, which is exactly what the expected-side
# parser produces for "TIMESTAMP WITH TIME ZONE" — that symmetry is what the
# matching test below relies on; do not normalize only one side.

PG_PARTIAL_INDEXDEF = (
    "CREATE INDEX ix_auth_sessions_user_expires_active ON public.auth_sessions "
    "USING btree (user_id, expires_at) WHERE (revoked_at IS NULL)"
)
PG_UNIQUE_INDEXDEF = (
    "CREATE UNIQUE INDEX ix_auth_sessions_session_token_hash "
    "ON public.auth_sessions USING btree (session_token_hash)"
)


def _narrow(snap, table):
    """Restrict a snapshot to one table (the dimension under test: indexes)."""
    return SchemaSnapshot(
        tables={table: snap.tables[table]},
        primary_keys={table: snap.primary_keys[table]},
        foreign_keys={table: snap.foreign_keys[table]},
        uniques={table: snap.uniques[table]},
        checks={table: snap.checks[table]},
        indexes={table: snap.indexes[table]},
        generated_columns={table: snap.generated_columns[table]},
    )


class _AuthSessionsInspector:
    """Hand-authored catalog facts for auth_sessions, as a live PG inspector
    reports them (datetime types are PG type instances so their str()
    rendering follows the exact live code path)."""

    def get_table_names(self):
        return ["auth_sessions"]

    def get_columns(self, table):
        from sqlalchemy.dialects import postgresql

        ts = postgresql.TIMESTAMP(timezone=True)
        return [
            {"name": "id", "type": "UUID", "nullable": False, "default": None},
            {"name": "session_token_hash", "type": "VARCHAR(64)", "nullable": False, "default": None},
            {"name": "user_id", "type": "INTEGER", "nullable": False, "default": None},
            {"name": "created_at", "type": ts, "nullable": False, "default": None},
            {"name": "last_seen_at", "type": ts, "nullable": False, "default": None},
            {"name": "expires_at", "type": ts, "nullable": False, "default": None},
            {"name": "revoked_at", "type": ts, "nullable": True, "default": None},
            {"name": "ip_address", "type": "VARCHAR(64)", "nullable": True, "default": None},
            {"name": "user_agent", "type": "VARCHAR(512)", "nullable": True, "default": None},
        ]

    def get_pk_constraint(self, table):
        return {"constrained_columns": ["id"]}

    def get_foreign_keys(self, table):
        return [{
            "constrained_columns": ["user_id"],
            "referred_table": "users",
            "referred_columns": ["id"],
            "options": {"ondelete": "CASCADE"},
        }]

    def get_unique_constraints(self, table):
        # The token-hash uniqueness is a standalone UNIQUE INDEX, not a
        # table constraint (matches the frozen baseline).
        return []

    def get_check_constraints(self, table):
        return []

    def get_indexes(self, table):
        return [
            {
                "name": "ix_auth_sessions_session_token_hash",
                "column_names": ["session_token_hash"],
                "unique": True,
            },
            {
                "name": "ix_auth_sessions_user_expires_active",
                "column_names": ["user_id", "expires_at"],
                "unique": False,
            },
        ]


def test_predicate_extraction_from_representative_indexdefs():
    # Partial index: extracted and normalized exactly like the baseline side.
    assert _adopt.predicate_from_indexdef(PG_PARTIAL_INDEXDEF) == "REVOKED_AT IS NULL"
    # Ordinary non-partial index: positively predicate-free (None, not unknown).
    assert _adopt.predicate_from_indexdef(PG_UNIQUE_INDEXDEF) is None
    # Empty WHERE clause: must raise (an empty predicate is not "no predicate").
    with pytest.raises(ValueError):
        _adopt.predicate_from_indexdef(
            "CREATE INDEX ix_x ON t USING btree (a) WHERE"
        )
    # Unbalanced/unclosable predicate: must raise rather than guess.
    with pytest.raises(ValueError):
        _adopt.predicate_from_indexdef(
            "CREATE INDEX ix_x ON t USING btree (a) WHERE (unbalanced"
        )


def test_matching_partial_and_plain_index_verify_clean():
    exp = _narrow(expected_from_baseline(), "auth_sessions")
    conn = _pg_conn([
        ("auth_sessions", "ix_auth_sessions_user_expires_active", PG_PARTIAL_INDEXDEF),
        ("auth_sessions", "ix_auth_sessions_session_token_hash", PG_UNIQUE_INDEXDEF),
    ])
    predicates = _adopt._index_predicates(conn)
    assert predicates["auth_sessions"]["ix_auth_sessions_user_expires_active"] == (
        "REVOKED_AT IS NULL"
    )
    # Ordinary non-partial index is recorded as positively predicate-free.
    assert predicates["auth_sessions"]["ix_auth_sessions_session_token_hash"] is None
    act = actual_from_inspector(_AuthSessionsInspector(), index_predicates=predicates)
    assert compare_snapshots(exp, act) == []


def test_index_predicate_mismatch_is_reported():
    exp = _narrow(expected_from_baseline(), "auth_sessions")
    bad = PG_PARTIAL_INDEXDEF.replace("IS NULL", "IS NOT NULL")
    conn = _pg_conn([
        ("auth_sessions", "ix_auth_sessions_user_expires_active", bad),
        ("auth_sessions", "ix_auth_sessions_session_token_hash", PG_UNIQUE_INDEXDEF),
    ])
    act = actual_from_inspector(
        _AuthSessionsInspector(), index_predicates=_adopt._index_predicates(conn)
    )
    diffs = compare_snapshots(exp, act)
    assert diffs, "predicate mismatch must be detected"
    assert any("predicate" in d and "auth_sessions" in d for d in diffs)


def test_missing_predicate_entry_fails_closed_unverifiable():
    # The partial index exists in the inspector but its definition is absent
    # from the pg_indexes result -> UNVERIFIABLE -> difference, never a match.
    exp = _narrow(expected_from_baseline(), "auth_sessions")
    conn = _pg_conn([
        ("auth_sessions", "ix_auth_sessions_session_token_hash", PG_UNIQUE_INDEXDEF),
    ])
    act = actual_from_inspector(
        _AuthSessionsInspector(), index_predicates=_adopt._index_predicates(conn)
    )
    diffs = compare_snapshots(exp, act)
    assert any("UNVERIFIABLE" in d for d in diffs)


def test_adopt_unparseable_predicate_aborts_without_write():
    # A WHERE clause that cannot be extracted must abort adoption (exit 3)
    # before any comparison result could trigger a write.
    engine = _adopt_engine(pg_rows=[(
        "auth_sessions",
        "ix_auth_sessions_user_expires_active",
        "CREATE INDEX ix_auth_sessions_user_expires_active "
        "ON public.auth_sessions USING btree (user_id, expires_at) WHERE",
    )])
    read_conn = engine.connect.return_value.__enter__.return_value
    with patch("adopt_schema.inspect", new=_adopt_inspector()), \
         patch("adopt_schema.engine", engine), \
         patch("adopt_schema.actual_from_inspector", return_value=expected_from_baseline()):
        rc = main([])
        assert rc == 3
        engine.begin.assert_not_called()
        _assert_no_writes(read_conn)
