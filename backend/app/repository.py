import sqlite3
from contextlib import closing
from uuid import uuid4
from decimal import Decimal

from app.schemas import VehicleCreate, VehicleResponse

def row_to_vehicle(row):
    return VehicleResponse(
        id=row["id"],
        make=row["make"],
        model=row["model"],
        category=row["category"],
        price=(
            Decimal(row["price_cents"]) / Decimal("100")
        ).quantize(Decimal("0.01")),
        quantity=row["quantity"],
    )

def create_vehicle(database_path, vehicle: VehicleCreate):
    vehicle_id = str(uuid4())
    price_cents = int(vehicle.price * 100)

    with closing(sqlite3.connect(database_path)) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO vehicles (
                    id,
                    make,
                    model,
                    category,
                    price_cents,
                    quantity
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    vehicle_id,
                    vehicle.make,
                    vehicle.model,
                    vehicle.category,
                    price_cents,
                    vehicle.quantity,
                ),
            )

    return VehicleResponse(
        id=vehicle_id,
        **vehicle.model_dump(),
    )
def list_vehicles(database_path):
    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT id, make, model, category, price_cents, quantity
            FROM vehicles
            ORDER BY make, model, id
            """
        ).fetchall()

    return [row_to_vehicle(row) for row in rows]

def update_vehicle(database_path, vehicle_id, vehicle: VehicleCreate):
    price_cents = int(vehicle.price * 100)

    with closing(sqlite3.connect(database_path)) as connection:
        with connection:
            cursor = connection.execute(
                """
                UPDATE vehicles
                SET make = ?,
                    model = ?,
                    category = ?,
                    price_cents = ?,
                    quantity = ?
                WHERE id = ?
                """,
                (
                    vehicle.make,
                    vehicle.model,
                    vehicle.category,
                    price_cents,
                    vehicle.quantity,
                    vehicle_id,
                ),
            )

            if cursor.rowcount == 0:
                return None

    return VehicleResponse(
        id=vehicle_id,
        **vehicle.model_dump(),
    )
def delete_vehicle(database_path, vehicle_id):
    with closing(sqlite3.connect(database_path)) as connection:
        with connection:
            cursor = connection.execute(
                """
                DELETE FROM vehicles
                WHERE id = ?
                """,
                (vehicle_id,),
            )

            return cursor.rowcount > 0
def search_vehicles(
    database_path,
    make=None,
    model=None,
    category=None,
    min_price=None,
    max_price=None,
):
    conditions = []
    parameters = []

    text_filters = {
        "make": make,
        "model": model,
        "category": category,
    }

    for column, value in text_filters.items():
        if value is not None:
            conditions.append(
                f"instr(lower({column}), lower(?)) > 0"
            )
            parameters.append(value)

    if min_price is not None:
        conditions.append("price_cents >= ?")
        parameters.append(int(min_price * 100))

    if max_price is not None:
        conditions.append("price_cents <= ?")
        parameters.append(int(max_price * 100))

    query = """
        SELECT id, make, model, category, price_cents, quantity
        FROM vehicles
    """

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY make, model, id"

    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            query,
            parameters,
        ).fetchall()

    return [row_to_vehicle(row) for row in rows]

def purchase_vehicle(database_path, vehicle_id, quantity):
    with closing(sqlite3.connect(database_path, timeout=10)) as connection:
        connection.row_factory = sqlite3.Row

        with connection:
            cursor = connection.execute(
                """
                UPDATE vehicles
                SET quantity = quantity - ?
                WHERE id = ?
                  AND quantity >= ?
                """,
                (quantity, vehicle_id, quantity),
            )

            row = connection.execute(
                """
                SELECT id, make, model, category, price_cents, quantity
                FROM vehicles
                WHERE id = ?
                """,
                (vehicle_id,),
            ).fetchone()

            if row is None:
                return None, "not_found"

            if cursor.rowcount == 0:
                return None, "insufficient_stock"

            return row_to_vehicle(row), None

def restock_vehicle(database_path, vehicle_id, quantity):
    with closing(sqlite3.connect(database_path, timeout=10)) as connection:
        connection.row_factory = sqlite3.Row

        with connection:
            cursor = connection.execute(
                """
                UPDATE vehicles
                SET quantity = quantity + ?
                WHERE id = ?
                  AND quantity + ? <= 1000000
                """,
                (quantity, vehicle_id, quantity),
            )

            row = connection.execute(
                """
                SELECT id, make, model, category, price_cents, quantity
                FROM vehicles
                WHERE id = ?
                """,
                (vehicle_id,),
            ).fetchone()

            if row is None:
                return None, "not_found"

            if cursor.rowcount == 0:
                return None, "stock_limit_exceeded"

            return row_to_vehicle(row), None