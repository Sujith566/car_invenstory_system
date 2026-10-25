import sqlite3
import pytest
from contextlib import closing

from fastapi.testclient import TestClient
from concurrent.futures import ThreadPoolExecutor
from app.main import create_app


def test_add_vehicle_saves_to_database(tmp_path):
    database_path = tmp_path / "inventory.db"
    app = create_app(database_path)

    vehicle_data = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": "25000.50",
        "quantity": 3,
    }

    with TestClient(app) as client:
        authenticate_admin(client)
        response = client.post(
            "/api/vehicles",
            json=vehicle_data,
        )

    assert response.status_code == 201

    saved_vehicle = response.json()

    assert saved_vehicle["id"]
    assert saved_vehicle["make"] == "Toyota"
    assert saved_vehicle["model"] == "Camry"
    assert saved_vehicle["category"] == "Sedan"
    assert saved_vehicle["price"] == "25000.50"
    assert saved_vehicle["quantity"] == 3

    # Verify that the API actually saved the vehicle.
    with closing(sqlite3.connect(database_path)) as connection:
        row = connection.execute(
            """
            SELECT make, model, price_cents, quantity
            FROM vehicles
            WHERE id = ?
            """,
            (saved_vehicle["id"],),
        ).fetchone()

    assert row == ("Toyota", "Camry", 2500050, 3)

@pytest.mark.parametrize(
    "invalid_field",
    [
        {"make": ""},
        {"make": "   "},
        {"model": ""},
        {"category": ""},
        {"price": "-1.00"},
        {"price": "10.999"},
        {"quantity": -1},
        {"quantity": 1.5},
        {"quantity": "3"},
    ],
)
def test_add_vehicle_rejects_invalid_data(tmp_path, invalid_field):
    database_path = tmp_path / "inventory.db"
    app = create_app(database_path)

    vehicle_data = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": "25000.50",
        "quantity": 3,
    }

    vehicle_data.update(invalid_field)

    with TestClient(app) as client:
        authenticate_admin(client)        
        response = client.post(
            "/api/vehicles",
            json=vehicle_data,
        )

    assert response.status_code == 422

def test_list_vehicles_returns_empty_list(tmp_path):
    database_path = tmp_path / "inventory.db"
    app = create_app(database_path)

    with TestClient(app) as client:
        authenticate_admin(client)        
    response = client.get("/api/vehicles")
    assert response.status_code == 200
    assert response.json() == []


def test_list_vehicles_returns_saved_vehicles(tmp_path):
    database_path = tmp_path / "inventory.db"
    app = create_app(database_path)

    vehicle_data = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": "25000.50",
        "quantity": 3,
    }

    with TestClient(app) as client:
        authenticate_admin(client)        
        create_response = client.post(
            "/api/vehicles",
            json=vehicle_data,
        )

        assert create_response.status_code == 201

        response = client.get("/api/vehicles")

    assert response.status_code == 200
    assert response.json() == [create_response.json()]

def test_update_vehicle_saves_changes(tmp_path):
    database_path = tmp_path / "inventory.db"
    app = create_app(database_path)

    original_data = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": "25000.50",
        "quantity": 3,
    }

    updated_data = {
        "make": "Toyota",
        "model": "Corolla",
        "category": "Sedan",
        "price": "22000.00",
        "quantity": 5,
    }

    with TestClient(app) as client:
        authenticate_admin(client)        
        create_response = client.post(
            "/api/vehicles",
            json=original_data,
        )
        assert create_response.status_code == 201

        vehicle_id = create_response.json()["id"]

        response = client.put(
            f"/api/vehicles/{vehicle_id}",
            json=updated_data,
        )

        assert response.status_code == 200
        assert response.json() == {
            "id": vehicle_id,
            **updated_data,
        }

        # A separate request verifies that changes were saved.
        list_response = client.get("/api/vehicles")

        assert list_response.status_code == 200
        assert list_response.json() == [
            {"id": vehicle_id, **updated_data}
        ]


def test_update_missing_vehicle_returns_404(tmp_path):
    database_path = tmp_path / "inventory.db"
    app = create_app(database_path)

    vehicle_data = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": "25000.50",
        "quantity": 3,
    }

    with TestClient(app) as client:
        authenticate_admin(client)        
        response = client.put(
            "/api/vehicles/nonexistent-id",
            json=vehicle_data,
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Vehicle not found"
    }
def test_delete_vehicle_removes_it(tmp_path):
    database_path = tmp_path / "inventory.db"
    app = create_app(database_path)

    vehicle_data = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": "25000.50",
        "quantity": 3,
    }

    with TestClient(app) as client:
        authenticate_admin(client)        
        create_response = client.post(
            "/api/vehicles",
            json=vehicle_data,
        )
        assert create_response.status_code == 201

        vehicle_id = create_response.json()["id"]

        response = client.delete(
            f"/api/vehicles/{vehicle_id}"
        )

        assert response.status_code == 204
        assert response.content == b""

        list_response = client.get("/api/vehicles")

        assert list_response.status_code == 200
        assert list_response.json() == []


def test_delete_missing_vehicle_returns_404(tmp_path):
    database_path = tmp_path / "inventory.db"
    app = create_app(database_path)

    with TestClient(app) as client:
        authenticate_admin(client)        
        response = client.delete(
            "/api/vehicles/nonexistent-id"
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Vehicle not found"
    }
def test_search_vehicles_by_make(tmp_path):
    database_path = tmp_path / "inventory.db"
    app = create_app(database_path)

    vehicles = [
        {
            "make": "Toyota",
            "model": "Camry",
            "category": "Sedan",
            "price": "25000.50",
            "quantity": 3,
        },
        {
            "make": "Honda",
            "model": "Civic",
            "category": "Sedan",
            "price": "23000.00",
            "quantity": 2,
        },
    ]

    with TestClient(app) as client:
        authenticate_admin(client)        
        for vehicle in vehicles:
            response = client.post(
                "/api/vehicles",
                json=vehicle,
            )
            assert response.status_code == 201

        response = client.get(
            "/api/vehicles/search",
            params={"make": "toy"},
        )

    assert response.status_code == 200

    results = response.json()

    assert len(results) == 1
    assert results[0]["make"] == "Toyota"
    assert results[0]["model"] == "Camry"


def test_search_vehicles_returns_empty_when_no_match(tmp_path):
    database_path = tmp_path / "inventory.db"
    app = create_app(database_path)

    vehicle_data = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": "25000.50",
        "quantity": 3,
    }

    with TestClient(app) as client:
        authenticate_admin(client)        
        response = client.post(
            "/api/vehicles",
            json=vehicle_data,
        )
        assert response.status_code == 201

        response = client.get(
            "/api/vehicles/search",
            params={"make": "BMW"},
        )

    assert response.status_code == 200
    assert response.json() == []
@pytest.mark.parametrize(
    "filters, expected_models",
    [
        ({"model": "civ"}, ["Civic"]),
        ({"category": "suv"}, ["RAV4"]),
        ({"min_price": "26000.00"}, ["RAV4"]),
        (
            {"max_price": "25000.50"},
            ["Civic", "Camry"],
        ),
        (
            {
                "make": "toy",
                "category": "sedan",
                "min_price": "25000.50",
                "max_price": "25000.50",
            },
            ["Camry"],
        ),
        (
            {"make": "Toyota", "category": "Hatchback"},
            [],
        ),
    ],
)
def test_search_vehicles_with_filters(
    tmp_path,
    filters,
    expected_models,
):
    app = create_app(tmp_path / "inventory.db")

    vehicles = [
        {
            "make": "Toyota",
            "model": "Camry",
            "category": "Sedan",
            "price": "25000.50",
            "quantity": 3,
        },
        {
            "make": "Toyota",
            "model": "RAV4",
            "category": "SUV",
            "price": "30000.00",
            "quantity": 2,
        },
        {
            "make": "Honda",
            "model": "Civic",
            "category": "Sedan",
            "price": "23000.00",
            "quantity": 1,
        },
    ]

    with TestClient(app) as client:
        authenticate_admin(client)        
        for vehicle in vehicles:
            response = client.post(
                "/api/vehicles",
                json=vehicle,
            )
            assert response.status_code == 201

        response = client.get(
            "/api/vehicles/search",
            params=filters,
        )

    assert response.status_code == 200

    models = [
        vehicle["model"]
        for vehicle in response.json()
    ]

    assert models == expected_models
@pytest.mark.parametrize(
    "starting_quantity, purchase_quantity, expected_quantity",
    [
        (5, 2, 3),
        (1, 1, 0),
    ],
)
def test_purchase_reduces_stock(
    tmp_path,
    starting_quantity,
    purchase_quantity,
    expected_quantity,
):
    app = create_app(tmp_path / "inventory.db")

    vehicle_data = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": "25000.50",
        "quantity": starting_quantity,
    }

    with TestClient(app) as client:
        authenticate_admin(client)        
        created = client.post(
            "/api/vehicles",
            json=vehicle_data,
        )
        assert created.status_code == 201

        vehicle_id = created.json()["id"]

        response = client.post(
            f"/api/vehicles/{vehicle_id}/purchase",
            json={"quantity": purchase_quantity},
        )

        assert response.status_code == 200
        assert response.json()["id"] == vehicle_id
        assert response.json()["quantity"] == expected_quantity

        saved = client.get("/api/vehicles")

        assert saved.status_code == 200
        assert saved.json()[0]["quantity"] == expected_quantity


@pytest.mark.parametrize(
    "starting_quantity, purchase_quantity",
    [
        (0, 1),
        (2, 3),
    ],
)
def test_purchase_rejects_insufficient_stock(
    tmp_path,
    starting_quantity,
    purchase_quantity,
):
    app = create_app(tmp_path / "inventory.db")

    vehicle_data = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": "25000.50",
        "quantity": starting_quantity,
    }

    with TestClient(app) as client:
        authenticate_admin(client)        
        created = client.post(
            "/api/vehicles",
            json=vehicle_data,
        )
        assert created.status_code == 201

        vehicle_id = created.json()["id"]

        response = client.post(
            f"/api/vehicles/{vehicle_id}/purchase",
            json={"quantity": purchase_quantity},
        )

        assert response.status_code == 409
        assert response.json() == {
            "detail": "Insufficient stock"
        }

        # A failed purchase must not change stock.
        saved = client.get("/api/vehicles")

        assert saved.status_code == 200
        assert saved.json()[0]["quantity"] == starting_quantity


def test_purchase_missing_vehicle_returns_404(tmp_path):
    app = create_app(tmp_path / "inventory.db")

    with TestClient(app) as client:
        authenticate_admin(client)        
        response = client.post(
            "/api/vehicles/nonexistent-id/purchase",
            json={"quantity": 1},
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Vehicle not found"
    }


@pytest.mark.parametrize(
    "invalid_quantity",
    [0, -1, 1.5, "2", True, 1000001],
)
def test_purchase_rejects_invalid_quantity(
    tmp_path,
    invalid_quantity,
):
    app = create_app(tmp_path / "inventory.db")

    vehicle_data = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": "25000.50",
        "quantity": 3,
    }

    with TestClient(app) as client:
        authenticate_admin(client)        
        created = client.post(
            "/api/vehicles",
            json=vehicle_data,
        )
        assert created.status_code == 201

        vehicle_id = created.json()["id"]

        response = client.post(
            f"/api/vehicles/{vehicle_id}/purchase",
            json={"quantity": invalid_quantity},
        )

        assert response.status_code == 422

        saved = client.get("/api/vehicles")

        assert saved.status_code == 200
        assert saved.json()[0]["quantity"] == 3
def test_simultaneous_purchases_cannot_oversell(tmp_path):
    app = create_app(tmp_path / "inventory.db")

    vehicle_data = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": "25000.50",
        "quantity": 1,
    }

    with TestClient(app) as client:
        authenticate_admin(client)        
        created = client.post(
            "/api/vehicles",
            json=vehicle_data,
        )
        assert created.status_code == 201

        vehicle_id = created.json()["id"]

        def purchase_one():
            response = client.post(
                f"/api/vehicles/{vehicle_id}/purchase",
                json={"quantity": 1},
            )
            return response.status_code

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(purchase_one)
                for _ in range(2)
            ]

            statuses = sorted(
                future.result()
                for future in futures
            )

        assert statuses == [200, 409]

        saved = client.get("/api/vehicles")

        assert saved.status_code == 200
        assert saved.json()[0]["quantity"] == 0
def test_restock_increases_quantity(tmp_path):
    app = create_app(tmp_path / "inventory.db")

    vehicle_data = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": "25000.50",
        "quantity": 0,
    }

    with TestClient(app) as client:
        authenticate_admin(client)        
        created = client.post(
            "/api/vehicles",
            json=vehicle_data,
        )
        assert created.status_code == 201

        vehicle_id = created.json()["id"]

        response = client.post(
            f"/api/vehicles/{vehicle_id}/restock",
            json={"quantity": 5},
        )

        assert response.status_code == 200
        assert response.json()["id"] == vehicle_id
        assert response.json()["quantity"] == 5

        saved = client.get("/api/vehicles")

        assert saved.status_code == 200
        assert saved.json()[0]["quantity"] == 5


def test_restock_missing_vehicle_returns_404(tmp_path):
    app = create_app(tmp_path / "inventory.db")

    with TestClient(app) as client:
        authenticate_admin(client)        
        response = client.post(
            "/api/vehicles/nonexistent-id/restock",
            json={"quantity": 5},
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Vehicle not found"
    }


@pytest.mark.parametrize(
    "invalid_quantity",
    [0, -1, 1.5, "2", True, 1000001],
)
def test_restock_rejects_invalid_quantity(
    tmp_path,
    invalid_quantity,
):
    app = create_app(tmp_path / "inventory.db")

    vehicle_data = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": "25000.50",
        "quantity": 3,
    }

    with TestClient(app) as client:
        authenticate_admin(client)        
        created = client.post(
            "/api/vehicles",
            json=vehicle_data,
        )
        assert created.status_code == 201

        vehicle_id = created.json()["id"]

        response = client.post(
            f"/api/vehicles/{vehicle_id}/restock",
            json={"quantity": invalid_quantity},
        )

        assert response.status_code == 422

        saved = client.get("/api/vehicles")

        assert saved.status_code == 200
        assert saved.json()[0]["quantity"] == 3


def test_restock_rejects_total_above_stock_limit(tmp_path):
    app = create_app(tmp_path / "inventory.db")

    vehicle_data = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": "25000.50",
        "quantity": 999999,
    }

    with TestClient(app) as client:
        authenticate_admin(client)        
        created = client.post(
            "/api/vehicles",
            json=vehicle_data,
        )
        assert created.status_code == 201

        vehicle_id = created.json()["id"]

        response = client.post(
            f"/api/vehicles/{vehicle_id}/restock",
            json={"quantity": 2},
        )

        assert response.status_code == 409
        assert response.json() == {
            "detail": "Stock limit exceeded"
        }

        saved = client.get("/api/vehicles")

        assert saved.status_code == 200
        assert saved.json()[0]["quantity"] == 999999

def authenticate_admin(client):
    credentials = {
        "email": "admin@example.com",
        "password": "StrongPassword123!",
    }

    registered = client.post(
        "/api/auth/register",
        json=credentials,
    )
    assert registered.status_code == 201

    with closing(
        sqlite3.connect(client.app.state.database_path)
    ) as connection:
        with connection:
            connection.execute(
                """
                UPDATE users
                SET is_admin = 1
                WHERE id = ?
                """,
                (registered.json()["id"],),
            )

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

def authenticate_admin(client):
    credentials = {
        "email": "admin@example.com",
        "password": "StrongPassword123!",
    }

    registered = client.post(
        "/api/auth/register",
        json=credentials,
    )
    assert registered.status_code == 201

    with closing(
        sqlite3.connect(client.app.state.database_path)
    ) as connection:
        with connection:
            connection.execute(
                "UPDATE users SET is_admin = 1 WHERE id = ?",
                (registered.json()["id"],),
            )

    login = client.post(
        "/api/auth/login",
        json=credentials,
    )
    assert login.status_code == 200

    token = login.json()["access_token"]

    client.headers.update(
        {"Authorization": f"Bearer {token}"}
    )