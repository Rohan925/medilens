import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
from uuid import UUID, uuid4

import psycopg
from fastapi import HTTPException, Request, status

from app.services.db import get_connection


logger = logging.getLogger("auth")

AUTH_COOKIE_NAME = "medilens_auth"
AUTH_MAX_AGE_SECONDS = 60 * 60 * 24 * 7
PBKDF2_ITERATIONS = 200_000
DEFAULT_AUTH_SECRET = "change-me-for-production"


@dataclass
class UserRecord:
    id: str
    email: str
    password_hash: str


def _get_auth_secret() -> bytes:
    return os.getenv("AUTH_SECRET", DEFAULT_AUTH_SECRET).encode("utf-8")


def _b64url_encode(raw_bytes: bytes) -> str:
    return base64.urlsafe_b64encode(raw_bytes).decode("utf-8").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return f"{PBKDF2_ITERATIONS}${salt.hex()}${derived_key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        iterations_raw, salt_hex, digest_hex = stored_hash.split("$", 2)
        iterations = int(iterations_raw)
        salt = bytes.fromhex(salt_hex)
        expected_digest = bytes.fromhex(digest_hex)
    except (ValueError, TypeError):
        return False

    candidate_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(candidate_digest, expected_digest)


def create_auth_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": int((datetime.now(UTC) + timedelta(seconds=AUTH_MAX_AGE_SECONDS)).timestamp()),
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = _b64url_encode(payload_bytes)
    signature = hmac.new(_get_auth_secret(), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    return f"{payload_b64}.{_b64url_encode(signature)}"


def verify_auth_token(token: str) -> str | None:
    try:
        payload_b64, signature_b64 = token.split(".", 1)
    except ValueError:
        return None

    expected_signature = hmac.new(
        _get_auth_secret(),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    try:
        provided_signature = _b64url_decode(signature_b64)
    except Exception:
        return None

    if not hmac.compare_digest(expected_signature, provided_signature):
        return None

    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except Exception:
        return None

    exp = payload.get("exp")
    sub = payload.get("sub")
    if not isinstance(exp, int) or not isinstance(sub, str):
        return None
    if exp < int(datetime.now(UTC).timestamp()):
        return None
    return sub


def _row_to_user(row: tuple[UUID, str, str] | None) -> UserRecord | None:
    if row is None:
        return None
    user_id, email, password_hash = row
    return UserRecord(
        id=str(user_id),
        email=email,
        password_hash=password_hash,
    )


def get_user_by_email(email: str) -> UserRecord | None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, email, password_hash FROM users WHERE email = %s",
                (email,),
            )
            return _row_to_user(cursor.fetchone())


def get_user_by_id(user_id: str) -> UserRecord | None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, email, password_hash FROM users WHERE id = %s",
                (user_id,),
            )
            return _row_to_user(cursor.fetchone())


def create_user(email: str, password: str) -> UserRecord:
    email_normalized = email.strip().lower()
    password_hash = hash_password(password)
    new_user_id = uuid4()

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (id, email, password_hash)
                    VALUES (%s, %s, %s)
                    RETURNING id, email, password_hash
                    """,
                    (new_user_id, email_normalized, password_hash),
                )
                row = cursor.fetchone()
            connection.commit()
    except psycopg.errors.UniqueViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from exc

    user = _row_to_user(row)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account.",
        )
    return user


def authenticate_user(email: str, password: str) -> UserRecord | None:
    user = get_user_by_email(email.strip().lower())
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def require_authenticated_user(request: Request) -> UserRecord:
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )

    user_id = verify_auth_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session.",
        )

    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User session is no longer valid.",
        )

    return user
