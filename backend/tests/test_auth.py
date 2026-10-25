import sqlite3
from contextlib import closing

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt

def test_register_creates_user(tmp_path):
    database_path = tmp_path / "inventory.db"
    app = create_app(database_path)

    with TestClient(app) as client:
        response = client.post(
            "/api/auth/register",
            json={
                "email": "Sujith@example.com",
                "password": "StrongPassword123!",
            },
        )

    assert response.status_code == 201

    user = response.json()

    assert user["id"]
    assert user["email"] == "sujith@example.com"
    assert user["is_admin"] is False
    assert "password" not in user
    assert "password_hash" not in user

    with closing(sqlite3.connect(database_path)) as connection:
        row = connection.execute(
            """
            SELECT email, password_hash, is_admin
            FROM users
            WHERE id = ?
            """,
            (user["id"],),
        ).fetchone()

    assert row is not None
    assert row[0] == "sujith@example.com"
    assert row[1]
    assert row[1] != "StrongPassword123!"
    assert row[2] == 0


def test_register_rejects_duplicate_email(tmp_path):
    app = create_app(tmp_path / "inventory.db")

    with TestClient(app) as client:
        first = client.post(
            "/api/auth/register",
            json={
                "email": "sujith@example.com",
                "password": "StrongPassword123!",
            },
        )
        assert first.status_code == 201

        duplicate = client.post(
            "/api/auth/register",
            json={
                "email": "SUJITH@example.com",
                "password": "AnotherPassword123!",
            },
        )

    assert duplicate.status_code == 409
    assert duplicate.json() == {
        "detail": "Email already registered"
    }


@pytest.mark.parametrize(
    "invalid_data",
    [
        {
            "email": "invalid-email",
            "password": "StrongPassword123!",
        },
        {
            "email": "sujith@example.com",
            "password": "short",
        },
        {
            "email": "sujith@example.com",
        },
        {
            "email": "sujith@example.com",
            "password": "StrongPassword123!",
            "is_admin": True,
        },
    ],
)
def test_register_rejects_invalid_input(tmp_path, invalid_data):
    app = create_app(tmp_path / "inventory.db")

    with TestClient(app) as client:
        response = client.post(
            "/api/auth/register",
            json=invalid_data,
        )

    assert response.status_code == 422

def test_login_returns_access_token(tmp_path):
    app = create_app(tmp_path / "inventory.db")

    credentials = {
        "email": "sujith@example.com",
        "password": "StrongPassword123!",
    }

    with TestClient(app) as client:
        registered = client.post(
            "/api/auth/register",
            json=credentials,
        )
        assert registered.status_code == 201

        response = client.post(
            "/api/auth/login",
            json=credentials,
        )

    assert response.status_code == 200

    result = response.json()

    assert isinstance(result["access_token"], str)
    assert result["access_token"]
    assert result["token_type"] == "bearer"
    assert "password" not in result
    assert "password_hash" not in result


@pytest.mark.parametrize(
    "email, password",
    [
        ("sujith@example.com", "WrongPassword123!"),
        ("unknown@example.com", "StrongPassword123!"),
    ],
)
def test_login_rejects_invalid_credentials(
    tmp_path,
    email,
    password,
):
    app = create_app(tmp_path / "inventory.db")

    with TestClient(app) as client:
        registered = client.post(
            "/api/auth/register",
            json={
                "email": "sujith@example.com",
                "password": "StrongPassword123!",
            },
        )
        assert registered.status_code == 201

        response = client.post(
            "/api/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid email or password"
    }


def test_login_accepts_email_with_different_case(tmp_path):
    app = create_app(tmp_path / "inventory.db")

    with TestClient(app) as client:
        registered = client.post(
            "/api/auth/register",
            json={
                "email": "sujith@example.com",
                "password": "StrongPassword123!",
            },
        )
        assert registered.status_code == 201

        response = client.post(
            "/api/auth/login",
            json={
                "email": "SUJITH@example.com",
                "password": "StrongPassword123!",
            },
        )

    assert response.status_code == 200
    assert response.json()["access_token"]

def test_me_returns_signed_in_user(tmp_path):
    app = create_app(tmp_path / "inventory.db")

    credentials = {
        "email": "sujith@example.com",
        "password": "StrongPassword123!",
    }

    with TestClient(app) as client:
        registered = client.post(
            "/api/auth/register",
            json=credentials,
        )
        assert registered.status_code == 201

        login = client.post(
            "/api/auth/login",
            json=credentials,
        )
        assert login.status_code == 200

        token = login.json()["access_token"]

        response = client.get(
            "/api/auth/me",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

    assert response.status_code == 200
    assert response.json() == registered.json()


def test_me_rejects_missing_token(tmp_path):
    app = create_app(tmp_path / "inventory.db")

    with TestClient(app) as client:
        response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_me_rejects_invalid_token(tmp_path):
    app = create_app(tmp_path / "inventory.db")

    with TestClient(app) as client:
        response = client.get(
            "/api/auth/me",
            headers={
                "Authorization": "Bearer invalid-token"
            },
        )

    assert response.status_code == 401

@pytest.mark.parametrize(
    "scenario",
    [
        "expired",
        "wrong_signature",
        "wrong_issuer",
        "missing_expiry",
        "unknown_user",
    ],
)
def test_me_rejects_untrusted_tokens(tmp_path, scenario):
    app = create_app(tmp_path / "inventory.db")

    with TestClient(app) as client:
        registered = client.post(
            "/api/auth/register",
            json={
                "email": "sujith@example.com",
                "password": "StrongPassword123!",
            },
        )
        assert registered.status_code == 201

        now = datetime.now(timezone.utc)

        payload = {
            "sub": registered.json()["id"],
            "iat": now,
            "exp": now + timedelta(hours=1),
            "iss": "car-inventory",
        }

        signing_secret = app.state.jwt_secret

        if scenario == "expired":
            payload["iat"] = now - timedelta(hours=2)
            payload["exp"] = now - timedelta(hours=1)

        elif scenario == "wrong_signature":
            signing_secret = (
                "different-secret-with-at-least-32-characters"
            )

        elif scenario == "wrong_issuer":
            payload["iss"] = "another-application"

        elif scenario == "missing_expiry":
            del payload["exp"]

        elif scenario == "unknown_user":
            payload["sub"] = str(uuid4())

        token = jwt.encode(
            payload,
            signing_secret,
            algorithm="HS256",
        )

        response = client.get(
            "/api/auth/me",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"