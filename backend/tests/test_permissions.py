import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.mark.parametrize(
    "method, path, body",
    [
        ("GET", "/api/vehicles", None),
        ("GET", "/api/vehicles/search", None),
        (
            "POST",
            "/api/vehicles",
            {
                "make": "Toyota",
                "model": "Camry",
                "category": "Sedan",
                "price": "25000.50",
                "quantity": 3,
            },
        ),
        (
            "PUT",
            "/api/vehicles/example-id",
            {
                "make": "Toyota",
                "model": "Camry",
                "category": "Sedan",
                "price": "25000.50",
                "quantity": 3,
            },
        ),
        ("DELETE", "/api/vehicles/example-id", None),
        (
            "POST",
            "/api/vehicles/example-id/purchase",
            {"quantity": 1},
        ),
        (
            "POST",
            "/api/vehicles/example-id/restock",
            {"quantity": 1},
        ),
    ],
)
def test_vehicle_routes_require_login(
    tmp_path,
    method,
    path,
    body,
):
    app = create_app(tmp_path / "inventory.db")

    with TestClient(app) as client:
        response = client.request(
            method,
            path,
            json=body,
        )

    assert response.status_code == 401


def test_regular_user_can_purchase_but_cannot_delete_or_restock(
    tmp_path,
):
    app = create_app(tmp_path / "inventory.db")

    credentials = {
        "email": "member@example.com",
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

        client.headers.update(
            {
                "Authorization": (
                    f"Bearer {login.json()['access_token']}"
                )
            }
        )

        created = client.post(
            "/api/vehicles",
            json={
                "make": "Toyota",
                "model": "Camry",
                "category": "Sedan",
                "price": "25000.50",
                "quantity": 3,
            },
        )
        assert created.status_code == 201

        vehicle_id = created.json()["id"]
        path = f"/api/vehicles/{vehicle_id}"

        purchased = client.post(
            f"{path}/purchase",
            json={"quantity": 1},
        )
        assert purchased.status_code == 200
        assert purchased.json()["quantity"] == 2

        deleted = client.delete(path)
        assert deleted.status_code == 403

        restocked = client.post(
            f"{path}/restock",
            json={"quantity": 1},
        )
        assert restocked.status_code == 403

        inventory = client.get("/api/vehicles")
        assert inventory.status_code == 200
        assert inventory.json()[0]["quantity"] == 2