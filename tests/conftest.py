import os
import pytest

@pytest.fixture(autouse=True, scope="session")
def set_test_environment():
    """
    Ensure tests never accidentally use real external services.
    """
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    os.environ.setdefault("POSTGRES_URL", "postgresql://user:pass@localhost:5432/test")
    os.environ.setdefault("MLFLOW_TRACKING_URI", "http://localhost:5000")
