"""SQLAlchemy 2.0 declarative base and database session management."""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from backend.app.core.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""
    pass


if "sqlite" in settings.postgres_url or os.getenv("TESTING") == "1":
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
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
    """Create all tables in the database."""
    import backend.app.models.tables  # noqa: F401
    Base.metadata.create_all(bind=engine)
