import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Request
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.user_repository import get_user_by_id
import jwt

def hash_password(password):
    salt = secrets.token_bytes(16)

    password_hash = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=16384,
        r=8,
        p=1,
    )

    return (
        f"scrypt$16384$8$1$"
        f"{salt.hex()}${password_hash.hex()}"
    )

def verify_password(password, stored_hash):
    try:
        (
            algorithm,
            n,
            r,
            p,
            salt_hex,
            expected_hash_hex,
        ) = stored_hash.split("$")

        # Accept only the format our application generates.
        if (algorithm, n, r, p) != ("scrypt", "16384", "8", "1"):
            return False

        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(expected_hash_hex)

        if len(salt) != 16 or len(expected_hash) != 64:
            return False

        actual_hash = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=16384,
            r=8,
            p=1,
        )

        return hmac.compare_digest(
            actual_hash,
            expected_hash,
        )

    except (ValueError, TypeError, AttributeError):
        return False

def create_access_token(user_id, secret):
    now = datetime.now(timezone.utc)

    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(hours=1),
        "iss": "car-inventory",
    }

    return jwt.encode(
        payload,
        secret,
        algorithm="HS256",
    )

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
):
    authentication_error = HTTPException(
        status_code=401,
        detail="Invalid or expired authentication",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise authentication_error

    try:
        payload = jwt.decode(
            credentials.credentials,
            request.app.state.jwt_secret,
            algorithms=["HS256"],
            issuer="car-inventory",
            options={
                "require": ["sub", "iat", "exp", "iss"]
            },
        )
    except jwt.InvalidTokenError:
        raise authentication_error

    user = get_user_by_id(
        database_path=request.app.state.database_path,
        user_id=payload["sub"],
    )

    if user is None:
        raise authentication_error

    return user

def require_admin(user=Depends(get_current_user)):
    if not user["is_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Administrator permission required",
        )

    return user