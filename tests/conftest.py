import pytest

@pytest.fixture
def mock_db_session():
    # Mock setup
    session = "mock_session"
    yield session
    # Mock teardown
    pass

@pytest.fixture
def sample_material():
    return {
        "item_type": "PIPE",
        "size": "200mm",
        "material": "A106"
    }
