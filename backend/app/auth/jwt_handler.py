from __future__ import annotations

import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(
    user_id: str,
    email: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token for a user."""
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(hours=JWT_EXPIRATION_HOURS)

    payload: dict[str, Any] = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_token(token: str) -> dict[str, Any] | None:
    """Verify token and return user info."""
    return decode_access_token(token)


class TokenPayload:
    """Extracted token payload data."""

    def __init__(self, payload: dict[str, Any]):
        self.user_id: str = payload.get("sub", "")
        self.email: str = payload.get("email", "")
        self.role: str = payload.get("role", "viewer")
        self.expired: bool = False

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_operator(self) -> bool:
        return self.role in {"admin", "operator"}

    def can_perform_action(self, action: str) -> bool:
        ACTION_PERMISSIONS: dict[str, list[str]] = {
            "view": ["viewer", "operator", "admin"],
            "accept_recommendation": ["operator", "admin"],
            "force_assess": ["operator", "admin"],
            "configure_agent": ["operator", "admin"],
            "manage_users": ["admin"],
            "delete_shipment": ["admin"],
            "bulk_import": ["operator", "admin"],
        }
        allowed_roles = ACTION_PERMISSIONS.get(action, ["admin"])
        return self.role in allowed_roles
