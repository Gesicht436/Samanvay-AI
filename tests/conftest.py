import os

os.environ["TESTING"] = "1"

import pytest
from backend.main import app
from backend.app.models.base import Base, engine, SessionLocal, init_db
from backend.app.api.dependencies import get_db_session
from backend.app.services.seeder import seed_users_if_empty
import backend.app.models.tables  # noqa: F401


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db()
    db = SessionLocal()
    try:
        seed_users_if_empty(db)
    finally:
        db.close()
    yield


@pytest.fixture(autouse=True)
def override_db():
    def _get_test_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db_session] = _get_test_db
    yield
    app.dependency_overrides.pop(get_db_session, None)


@pytest.fixture
def mock_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_material():
    return {
        "item_type": "PIPE",
        "size": "200mm",
        "material": "A106",
    }
