"""Schema verification helpers for migration adoption and startup checks.

Two independent sources of truth are compared:

* ``expected_from_baseline()`` -- the frozen DDL parsed from
  ``backend.alembic.baseline_schema`` (exactly what revision 0001 applies).
* ``actual_from_inspector()`` -- what a live PostgreSQL catalog reports.

Both are normalized into the same ``SchemaSnapshot`` shape so differences are
reported deterministically.  This module imports only SQLAlchemy; it does not
import Alembic and never opens a connection itself.  Connecting to the catalog
and reading it is the caller's responsibility (see ``scripts/adopt_schema.py``).

Fail-closed rule: anything that cannot be positively verified is recorded as
``UNVERIFIABLE`` and surfaces as a difference, which stops adoption.  An
unverified fact is never treated as a match.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


UNVERIFIABLE = "UNVERIFIABLE"


@dataclass(frozen=True)
class ColumnFacts:
    """Normalized description of one table column."""

    type: str
    nullable: bool
    server_default: Optional[str] = None


@dataclass(frozen=True)
class IndexFacts:
    """Normalized description of one index."""

    columns: tuple[str, ...]
    unique: bool
    predicate: Optional[str] = None


@dataclass
class SchemaSnapshot:
    """Table -> facts map.  Used for both the expected and actual side."""

    tables: dict[str, dict[str, ColumnFacts]] = field(default_factory=dict)
    primary_keys: dict[str, tuple[str, ...]] = field(default_factory=dict)
    foreign_keys: dict[str, tuple[tuple[str, str, str, Optional[str]], ...]] = field(
        default_factory=dict
    )
    uniques: dict[str, tuple[tuple[str, ...], ...]] = field(default_factory=dict)
    checks: dict[str, tuple[tuple[str, ...], ...]] = field(default_factory=dict)
    indexes: dict[str, dict[str, IndexFacts]] = field(default_factory=dict)
    generated_columns: dict[str, tuple[str, ...]] = field(default_factory=dict)


_WS = re.compile(r"\s+")

_TYPE_ALIASES = {
    "TIMESTAMPWITHTIMEZONE": "TIMESTAMPTZ",
    "TIMESTAMPWITHOUTTIMEZONE": "TIMESTAMP",
    "CHARACTERVARYING": "VARCHAR",
}


def _norm_ws(text: str) -> str:
    return _WS.sub(" ", (text or "")).strip()


def normalize_type(type_str: str) -> str:
    """Collapse type spelling so baseline DDL and catalog reflection agree.

    ``SERIAL`` is PostgreSQL shorthand for an autoincrement INTEGER backed by a
    sequence; reflection reports the column as INTEGER, so both sides are
    normalized to INTEGER.  The sequence default is normalized separately.
    """
    t = _WS.sub("", type_str or "").upper()
    if t == "SERIAL":
        t = "INTEGER"
    # Normalize numeric type spacing: NUMERIC(14,2) -> NUMERIC(14, 2)
    t = re.sub(r"NUMERIC\((\d+),(\d+)\)", r"NUMERIC(\1, \2)", t)
    return _TYPE_ALIASES.get(t, t)


def normalize_default(default: Optional[str]) -> Optional[str]:
    """Normalize a server default for comparison.

    Sequence-backed autoincrement defaults (``nextval('...'::regclass)``) are
    the physical realization of SQLAlchemy ``autoincrement``; reflection always
    reports them while compiled baseline DDL writes bare ``SERIAL``.  They are
    therefore normalized to ``None`` on both sides.
    """
    if default is None:
        return None
    d = default.strip()
    if d == "":
        return None
    if d.upper().startswith("NEXTVAL("):
        return None
    d = d.strip("()").strip()
    d = re.sub(r"::[\w ]+$", "", d).strip()
    low = d.lower()
    if low == "true":
        return "true"
    if low == "false":
        return "false"
    return low


def normalize_predicate(predicate: Optional[str]) -> Optional[str]:
    """Normalize a partial-index WHERE predicate for comparison."""
    if predicate is None:
        return None
    return _WS.sub(" ", predicate.replace("(", " ( ").replace(")", " ) ")).strip().upper()


def check_tokens(sqltext: str) -> tuple[str, ...]:
    """Tokenize a CHECK expression so parenthesis/casing differences don't matter."""
    text = (sqltext or "").strip()
    while text.startswith("(") and text.endswith(")"):
        inner = text[1:-1]
        if _balanced(inner):
            text = inner.strip()
        else:
            break
    return tuple(t.upper() for t in _WS.sub(" ", text).split())


def _balanced(text: str) -> bool:
    depth = 0
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


# ── Expected side: parse the frozen baseline DDL ─────────────────────────────


def expected_from_baseline() -> SchemaSnapshot:
    """Build the expected snapshot by parsing the frozen baseline statements."""
    from backend.alembic.baseline_schema import BASELINE_STATEMENTS

    snap = SchemaSnapshot()
    for stmt in BASELINE_STATEMENTS:
        head = stmt.strip().upper()
        if head.startswith("CREATE TABLE"):
            _parse_create_table(stmt, snap)
        elif head.startswith("CREATE UNIQUE INDEX") or head.startswith("CREATE INDEX"):
            _parse_create_index(stmt, snap)
        else:
            raise ValueError(f"Unsupported baseline statement: {stmt[:60]!r}")
    return snap


def _parse_create_table(stmt: str, snap: SchemaSnapshot) -> None:
    m = re.match(r"CREATE TABLE (\w+) \((.*)\)\s*$", stmt.strip(), re.DOTALL)
    if not m:
        raise ValueError(f"Cannot parse CREATE TABLE: {stmt[:80]!r}")
    table = m.group(1)
    parts = _split_top_level(m.group(2))
    cols: dict[str, ColumnFacts] = {}
    pks: list[str] = []
    fks: list[tuple[str, str, str, Optional[str]]] = []
    uniques: list[tuple[str, ...]] = []
    checks: list[tuple[str, ...]] = []
    generated: list[str] = []
    for part in parts:
        p = part.strip()
        up = p.upper()
        if up.startswith("PRIMARY KEY"):
            pks = _cols_inside(p)
        elif up.startswith("FOREIGN KEY"):
            fks.append(_parse_fk(p))
        elif up.startswith("UNIQUE"):
            uniques.append(tuple(_cols_inside(p)))
        elif "CHECK" in up and up.startswith("CONSTRAINT"):
            checks.append(check_tokens(_check_inner(p)))
        else:
            name, facts = _parse_column(p)
            cols[name] = facts
            if "GENERATED" in up:
                generated.append(name)
    snap.tables[table] = cols
    snap.primary_keys[table] = tuple(pks)
    snap.foreign_keys[table] = tuple(fks)
    snap.uniques[table] = tuple(uniques)
    snap.checks[table] = tuple(checks)
    snap.generated_columns[table] = tuple(generated)
    snap.indexes.setdefault(table, {})


def _parse_create_index(stmt: str, snap: SchemaSnapshot) -> None:
    m = re.match(
        r"CREATE (UNIQUE )?INDEX (\w+) ON (\w+) \((.*?)\)(?:\s+WHERE\s+(.*))?\s*$",
        stmt.strip(),
        re.DOTALL,
    )
    if not m:
        raise ValueError(f"Cannot parse CREATE INDEX: {stmt[:80]!r}")
    table = m.group(3)
    snap.indexes.setdefault(table, {})[m.group(2)] = IndexFacts(
        columns=tuple(c.strip() for c in m.group(4).split(",")),
        unique=bool(m.group(1)),
        predicate=normalize_predicate(m.group(5)),
    )


def _split_top_level(body: str) -> list[str]:
    """Split a CREATE TABLE body on commas that are not inside parentheses."""
    parts: list[str] = []
    depth = 0
    buf: list[str] = []
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf))
    return parts


def _cols_inside(clause: str) -> list[str]:
    m = re.search(r"\((.*)\)", clause, re.DOTALL)
    return [] if not m else [c.strip() for c in m.group(1).split(",")]


def _parse_fk(clause: str) -> tuple[str, str, str, Optional[str]]:
    m = re.match(
        r"FOREIGN KEY\s*\((\w+)\)\s*REFERENCES\s+(\w+)\s*\((\w+)\)"
        r"(?:\s+ON DELETE\s+(\w+(?:\s+NULL)?))?",
        clause.strip(),
    )
    if not m:
        raise ValueError(f"Cannot parse FK: {clause!r}")
    action = m.group(4)
    return (m.group(1), m.group(2), m.group(3), action.upper() if action else None)


def _check_inner(clause: str) -> str:
    m = re.search(r"CHECK\s+\((.*)\)\s*$", clause.strip(), re.DOTALL)
    return m.group(1) if m else ""


def _parse_column(part: str) -> tuple[str, ColumnFacts]:
    m = re.match(r"(\w+)\s+(.+)$", part.strip(), re.DOTALL)
    if not m:
        raise ValueError(f"Cannot parse column: {part!r}")
    name = m.group(1)
    rest = m.group(2)
    up = rest.upper()
    tm = re.match(r"([A-Za-z][A-Za-z0-9_ ]*?\([^)]*\)|[A-Za-z][A-Za-z0-9_]*)", rest)
    type_str = tm.group(1).strip() if tm else rest
    # A trailing NOT NULL must not be swallowed into the DEFAULT expression.
    body = re.sub(r"NOT NULL\s*$", "", rest.strip()).strip()
    default = None
    dm = re.search(r"^.*\bDEFAULT\s+(.+)$", body, re.IGNORECASE)
    if dm:
        default = normalize_default(dm.group(1))
    return name, ColumnFacts(
        type=normalize_type(type_str),
        nullable="NOT NULL" not in up,
        server_default=default,
    )

# ── Actual side: read a live PostgreSQL catalog via SQLAlchemy reflection ────
#
# Known reflection limit: SQLAlchemy's Inspector does NOT expose partial-index
# predicates.  Rather than treat a missing predicate as a match (which would
# silently accept a non-partial or differently-partitioned index), the predicate
# is recorded as UNVERIFIABLE.  Callers that can supply the true predicate (see
# the pg_index query in scripts/adopt_schema.py) pass it via ``index_predicates``;
# without it, adoption fails closed.


def actual_from_inspector(inspector, index_predicates=None) -> SchemaSnapshot:
    """Build a snapshot from a SQLAlchemy ``Inspector`` over a live database.

    ``index_predicates`` maps ``table -> {index_name: predicate_text}`` for any
    predicate the caller could read directly from the catalog (``pg_index``).
    An index whose predicate is unknown keeps ``UNVERIFIABLE``, so comparison
    reports a difference and adoption stops.
    """
    supplied = index_predicates or {}
    snap = SchemaSnapshot()
    tables = set(inspector.get_table_names())

    for table in sorted(tables):
        cols: dict[str, ColumnFacts] = {}
        for c in inspector.get_columns(table):
            cols[c["name"]] = ColumnFacts(
                type=normalize_type(str(c["type"])),
                nullable=bool(c["nullable"]),
                server_default=normalize_default(c.get("default")),
            )
        snap.tables[table] = cols

        pk = inspector.get_pk_constraint(table) or {}
        snap.primary_keys[table] = tuple(pk.get("constrained_columns") or ())

        fks = []
        for fk in inspector.get_foreign_keys(table):
            cols_in = tuple(fk.get("constrained_columns") or ())
            cols_ref = tuple(fk.get("referred_columns") or ())
            if len(cols_in) != 1 or len(cols_ref) != 1:
                # Composite FKs are not representable by the baseline parser.
                fks.append(
                    (
                        cols_in[0] if cols_in else "",
                        fk.get("referred_table") or "",
                        cols_ref[0] if cols_ref else UNVERIFIABLE,
                        UNVERIFIABLE,
                    )
                )
                continue
            options = fk.get("options") or {}
            fks.append(
                (
                    cols_in[0],
                    fk.get("referred_table") or "",
                    cols_ref[0],
                    str(options.get("ondelete") or "").upper() or None,
                )
            )
        snap.foreign_keys[table] = tuple(fks)

        uniques = []
        for uq in inspector.get_unique_constraints(table):
            names = tuple(uq.get("column_names") or ())
            if names:
                uniques.append(names)
        snap.uniques[table] = tuple(uniques)

        checks = []
        for ck in inspector.get_check_constraints(table):
            text = ck.get("sqltext") or ck.get("expression")
            if text:
                checks.append(check_tokens(text))
        snap.checks[table] = tuple(checks)

        # Generated columns are not exposed by reflection either; they are only
        # positively confirmed when the caller supplies catalog information.
        snap.generated_columns[table] = ()

        idx_map: dict[str, IndexFacts] = {}
        known = supplied.get(table, {})
        for idx in inspector.get_indexes(table):
            name = idx.get("name") or ""
            idx_map[name] = IndexFacts(
                columns=tuple(idx.get("column_names") or ()),
                unique=bool(idx.get("unique")),
                predicate=normalize_predicate(known[name])
                if name in known
                else UNVERIFIABLE,
            )
        snap.indexes[table] = idx_map

    return snap


# ── Comparison ───────────────────────────────────────────────────────────────


def compare_snapshots(expected: SchemaSnapshot, actual: SchemaSnapshot) -> list[str]:
    """Return a sorted list of human-readable differences (empty == identical)."""
    diffs: list[str] = []

    exp_tables = set(expected.tables)
    act_tables = set(actual.tables)
    for t in sorted(exp_tables - act_tables):
        diffs.append(f"missing table: {t}")
    for t in sorted(act_tables - exp_tables):
        diffs.append(f"unexpected extra table: {t}")

    for t in sorted(exp_tables & act_tables):
        diffs.extend(_compare_table(t, expected, actual))

    return sorted(diffs)


def _compare_table(t: str, expected: SchemaSnapshot, actual: SchemaSnapshot) -> list[str]:
    diffs: list[str] = []

    exp_cols = expected.tables[t]
    act_cols = actual.tables[t]
    for c in sorted(set(exp_cols) - set(act_cols)):
        diffs.append(f"{t}: missing column {c}")
    for c in sorted(set(act_cols) - set(exp_cols)):
        diffs.append(f"{t}: unexpected column {c}")
    for c in sorted(set(exp_cols) & set(act_cols)):
        e, a = exp_cols[c], act_cols[c]
        if e.type != a.type:
            diffs.append(f"{t}.{c}: type {a.type} != baseline {e.type}")
        if e.nullable != a.nullable:
            diffs.append(f"{t}.{c}: nullable={a.nullable} != baseline {e.nullable}")
        if e.server_default != a.server_default:
            diffs.append(
                f"{t}.{c}: server default {a.server_default!r} != baseline {e.server_default!r}"
            )

    epk, apk = expected.primary_keys.get(t, ()), actual.primary_keys.get(t, ())
    if set(epk) != set(apk):
        diffs.append(f"{t}: primary key {apk} != baseline {epk}")

    efks = set(expected.foreign_keys.get(t, ()))
    afks = set(actual.foreign_keys.get(t, ()))
    for fk in sorted(efks - afks):
        diffs.append(f"{t}: missing/incorrect FK {fk}")
    for fk in sorted(afks - efks):
        diffs.append(f"{t}: unexpected FK {fk}")

    eu = {tuple(sorted(u)) for u in expected.uniques.get(t, ())}
    au = {tuple(sorted(u)) for u in actual.uniques.get(t, ())}
    for u in sorted(eu - au):
        diffs.append(f"{t}: missing UNIQUE {u}")
    for u in sorted(au - eu):
        diffs.append(f"{t}: unexpected UNIQUE {u}")

    ec = set(expected.checks.get(t, ()))
    ac = set(actual.checks.get(t, ()))
    for c in sorted(ec - ac):
        diffs.append(f"{t}: missing CHECK {' '.join(c)}")
    for c in sorted(ac - ec):
        diffs.append(f"{t}: unexpected CHECK {' '.join(c)}")

    eidx = _index_by_signature(expected.indexes.get(t, {}))
    aidx = _index_by_signature(actual.indexes.get(t, {}))
    for sig in sorted(set(eidx) - set(aidx)):
        diffs.append(f"{t}: missing index {sig}")
    for sig in sorted(set(aidx) - set(eidx)):
        diffs.append(f"{t}: unexpected index {sig}")
    for sig in sorted(set(eidx) & set(aidx)):
        e_pred, a_pred = eidx[sig].predicate, aidx[sig].predicate
        if a_pred == UNVERIFIABLE or e_pred != a_pred:
            diffs.append(
                f"{t}: index {sig} predicate {a_pred!r} != baseline {e_pred!r} "
                "(not positively verifiable -> stop)"
            )
    return diffs


def _index_by_signature(idx_map: dict) -> dict:
    """Key indexes by (unique, columns) so cosmetic index-name changes don't matter."""
    return {(facts.unique, facts.columns): facts for facts in idx_map.values()}

