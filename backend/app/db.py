import sqlite3
from contextlib import closing


def initialize_database(database_path):
    with closing(sqlite3.connect(database_path)) as connection:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS vehicles (
                    id TEXT PRIMARY KEY,
                    make TEXT NOT NULL,
                    model TEXT NOT NULL,
                    category TEXT NOT NULL,
                    price_cents INTEGER NOT NULL
                        CHECK (price_cents >= 0),
                    quantity INTEGER NOT NULL
                        CHECK (quantity >= 0)
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    is_admin INTEGER NOT NULL DEFAULT 0
                        CHECK (is_admin IN (0, 1))
                )
                """
            )