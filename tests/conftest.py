import pytest
from fastapi.testclient import TestClient

@pytest.fixture(scope="function")
def client():
    """Test client для FastAPI"""
    from main import app
    return TestClient(app)