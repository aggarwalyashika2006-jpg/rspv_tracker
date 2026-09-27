from datetime import datetime, timedelta, timezone
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from jose import JWTError, jwt

from pwdlib import PasswordHash


# ============================================================
# CONFIGURATION
# ============================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "local-development-secret-change-this-before-deployment",
)

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60


# ============================================================
# PASSWORD HASHING
# ============================================================

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Securely hash a password.

    pwdlib uses a modern password hashing algorithm
    and avoids the bcrypt/passlib compatibility issue.
    """

    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:

    try:

        return password_hash.verify(
            plain_password,
            hashed_password,
        )

    except Exception:

        return False


# ============================================================
# OAUTH2
# ============================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/login"
)


# ============================================================
# CREATE JWT TOKEN
# ============================================================

def create_access_token(
    data: dict,
):

    payload = data.copy()

    expire = datetime.now(
        timezone.utc
    ) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload["exp"] = expire

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


# ============================================================
# GET CURRENT USER
# ============================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,

        detail="Could not validate credentials.",

        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = payload.get("sub")

        email = payload.get("email")

        role = payload.get("role")

        if user_id is None:

            raise credentials_exception

        return {
            "user_id": int(user_id),
            "email": email,
            "role": role,
        }

    except (
        JWTError,
        ValueError,
        TypeError,
    ):

        raise credentials_exception


# ============================================================
# ORGANIZER AUTHORIZATION
# ============================================================

def require_organizer(
    current_user: dict = Depends(
        get_current_user
    ),
):

    if current_user["role"] != "ORGANIZER":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,

            detail=(
                "Organizer permissions are required "
                "for this operation."
            ),
        )

    return current_user