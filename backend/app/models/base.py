"""SQLAlchemy 2.0 declarative base and database session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator

from backend.app.core.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""
    pass


engine = create_engine(
    settings.postgres_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a database session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables in the database.

    Development/test bootstrap only.  Production deployments must NOT rely on
    this for schema creation or upgrades; they provision the schema explicitly
    via Alembic migrations (fresh installs) or scripts/adopt_schema.py
    (existing create_all() databases), and verify it at startup with
    verify_schema_version().
    """
    import backend.app.models.tables  # noqa: F401
    Base.metadata.create_all(bind=engine)


def verify_schema_version(engine_obj=None, expected_revision=None, required_tables=None) -> None:
    """Read-only production startup verification.  Never migrates or stamps.

    Fails closed (raises RuntimeError) when ANY of the following holds:

    * the ``alembic_version`` table is missing (version state absent), so the
      database is not migration-managed;
    * the recorded revision does not equal the single expected head
      (revision mismatch — including multiple/zero rows);
    * any required baseline table is missing from the catalog;
    * any verification error occurs while reading the catalog.

    This performs no DDL and writes nothing.  Schema changes remain an explicit
    deployment operation; this check only confirms the deployed schema is the
    one the application expects before serving traffic.
    """
    from sqlalchemy import inspect, text
    from backend.alembic.baseline_schema import BASELINE_REVISION, BASELINE_TABLES

    eng = engine_obj if engine_obj is not None else engine
    exp_rev = expected_revision or BASELINE_REVISION
    tables = required_tables if required_tables is not None else BASELINE_TABLES

    with eng.connect() as conn:
        insp = inspect(conn)

        if not insp.has_table("alembic_version"):
            raise RuntimeError(
                "Schema verification failed: 'alembic_version' is missing. "
                "The database is not migration-managed. Provision it with "
                "'alembic upgrade head' (fresh) or scripts/adopt_schema.py "
                "(existing create_all() database)."
            )

        rows = conn.execute(text("SELECT version_num FROM alembic_version")).fetchall()
        versions = sorted({r[0] for r in rows})
        if versions != [exp_rev]:
            raise RuntimeError(
                f"Schema verification failed: recorded revision(s) {versions} "
                f"!= expected head '{exp_rev}'. Run 'alembic upgrade head'."
            )

        existing = set(insp.get_table_names())
        missing = [t for t in tables if t not in existing]
        if missing:
            raise RuntimeError(
                f"Schema verification failed: missing required table(s): "
                f"{sorted(missing)}. The deployed schema does not match the "
                f"application baseline."
            )

