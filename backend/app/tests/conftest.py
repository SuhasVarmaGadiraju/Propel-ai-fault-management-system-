import pytest
from app import create_app


@pytest.fixture
def app():
    """
    Fixture providing a Flask application instance configured for testing.
    """
    app = create_app("testing")
    yield app


@pytest.fixture
def client(app):
    """
    Fixture providing a test client for simulating HTTP requests.
    """
    return app.test_client()
