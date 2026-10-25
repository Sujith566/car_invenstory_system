import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.db import initialize_database
from app.routes.auth import router as auth_router
from app.routes.vehicles import router as vehicles_router


DEFAULT_DATABASE_PATH = (
    Path(__file__).resolve().parent.parent / "inventory.db"
)


def create_app(database_path=None):
    selected_path = (
        Path(database_path)
        if database_path is not None
        else DEFAULT_DATABASE_PATH
    )

    @asynccontextmanager
    async def lifespan(application):
        jwt_secret = os.environ.get("JWT_SECRET", "")

        if len(jwt_secret) < 32:
            raise RuntimeError(
                "JWT_SECRET must contain at least 32 characters"
            )

        application.state.jwt_secret = jwt_secret

        initialize_database(selected_path)
        yield

    application = FastAPI(
        title="Car Dealership Inventory API",
        lifespan=lifespan,
    )

    application.state.database_path = selected_path

    application.include_router(auth_router)
    application.include_router(vehicles_router)

    @application.get("/api/health")
    def health_check():
        return {"status": "ok"}

    return application


app = create_app()