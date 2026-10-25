import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request

from app.schemas import RegisterRequest, UserResponse
from app.security import hash_password
from app.user_repository import create_user

from app.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

from app.user_repository import (
    create_user,
    get_user_by_email,
)

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    status_code=201,
    response_model=UserResponse,
)
def register_user(
    data: RegisterRequest,
    request: Request,
):
    password_hash = hash_password(data.password)

    try:
        return create_user(
            database_path=request.app.state.database_path,
            email=str(data.email),
            password_hash=password_hash,
        )
    except sqlite3.IntegrityError as error:
        if "users.email" in str(error):
            raise HTTPException(
                status_code=409,
                detail="Email already registered",
            ) from error

        raise

@router.post("/login")
def login_user(
    data: RegisterRequest,
    request: Request,
):
    user = get_user_by_email(
        database_path=request.app.state.database_path,
        email=str(data.email),
    )

    if user is None or not verify_password(
        data.password,
        user["password_hash"],
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    token = create_access_token(
        user_id=user["id"],
        secret=request.app.state.jwt_secret,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }

@router.get(
    "/me",
    response_model=UserResponse,
)
def read_current_user(
    user=Depends(get_current_user),
):
    return user