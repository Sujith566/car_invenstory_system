import pytest


@pytest.fixture(autouse=True)
def configure_test_secret(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET",
        "test-only-secret-not-for-real-deployment-12345",
    )