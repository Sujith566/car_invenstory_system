import sqlite3
from contextlib import closing
from uuid import uuid4

from app.schemas import UserResponse


def create_user(database_path, email, password_hash):
    user_id = str(uuid4())

    with closing(sqlite3.connect(database_path)) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO users (
                    id,
                    email,
                    password_hash
                )
                VALUES (?, ?, ?)
                """,
                (user_id, email, password_hash),
            )

    return UserResponse(
        id=user_id,
        email=email,
        is_admin=False,
    )

def get_user_by_email(database_path, email):
    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row

        row = connection.execute(
            """
            SELECT id, email, password_hash, is_admin
            FROM users
            WHERE email = ?
            """,
            (email,),
        ).fetchone()

    return dict(row) if row is not None else None

def get_user_by_id(database_path, user_id):
    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row

        row = connection.execute(
            """
            SELECT id, email, is_admin
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "email": row["email"],
        "is_admin": bool(row["is_admin"]),
    }