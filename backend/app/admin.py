import argparse
import sqlite3
from contextlib import closing

from app.db import initialize_database
from app.main import DEFAULT_DATABASE_PATH


def main():
    parser = argparse.ArgumentParser(
        description="Promote a registered user to administrator"
    )
    parser.add_argument("email")
    args = parser.parse_args()

    email = args.email.strip().lower()

    initialize_database(DEFAULT_DATABASE_PATH)

    with closing(
        sqlite3.connect(DEFAULT_DATABASE_PATH)
    ) as connection:
        with connection:
            cursor = connection.execute(
                """
                UPDATE users
                SET is_admin = 1
                WHERE email = ?
                """,
                (email,),
            )

    if cursor.rowcount == 0:
        parser.exit(
            1,
            "User not found. Register this email first.\n",
        )

    print(f"Administrator access granted to {email}")


if __name__ == "__main__":
    main()