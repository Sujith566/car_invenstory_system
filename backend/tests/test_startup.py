import sqlite3

from fastapi.testclient import TestClient

from app.main import create_app


def test_startup_creates_database(tmp_path):
    database_path = tmp_path / "inventory.db"

    app = create_app(database_path)

    with TestClient(app):
        assert database_path.exists()

        connection = sqlite3.connect(database_path)

        try:
            table = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name = 'vehicles'
                """
            ).fetchone()
        finally:
            connection.close()

        assert table == ("vehicles",)