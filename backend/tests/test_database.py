import sqlite3

from app.db import initialize_database


def test_database_persists_vehicle(tmp_path):
    database_path = tmp_path / "test_inventory.db"

    initialize_database(database_path)

    # Save a vehicle and commit the transaction.
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO vehicles (
                id, make, model, category, price_cents, quantity
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("vehicle-1", "Toyota", "Camry", "Sedan", 2500050, 3),
        )

    # Open a separate connection to check persistence.
    with sqlite3.connect(database_path) as connection:
        vehicle = connection.execute(
            """
            SELECT make, model, price_cents, quantity
            FROM vehicles
            WHERE id = ?
            """,
            ("vehicle-1",),
        ).fetchone()

    assert vehicle == ("Toyota", "Camry", 2500050, 3)