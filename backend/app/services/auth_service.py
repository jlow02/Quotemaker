"""
Purpose: JWT token creation/verification and password hashing.
         Called by the auth router and get_current_user dependency.
Owner: [Claude]
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt as _bcrypt
from jose import JWTError, jwt

from app.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Purpose: Verify a plain-text password against a stored bcrypt hash.
    Inputs: plain_password (str), hashed_password (str)
    Outputs: bool — True if match
    Owner: [Claude]
    """
    return _bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def hash_password(plain_password: str) -> str:
    """
    Purpose: Hash a plain-text password with bcrypt.
    Inputs: plain_password (str)
    Outputs: str — bcrypt hash
    Owner: [Claude]
    """
    return _bcrypt.hashpw(plain_password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def create_access_token(subject: str) -> str:
    """
    Purpose: Create a short-lived JWT access token for the given subject (user_id as str).
    Inputs: subject (str) — typically str(user.id)
    Outputs: str — encoded JWT
    Owner: [Claude]
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {"sub": subject, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> str:
    """
    Purpose: Create a long-lived JWT refresh token for the given subject (user_id as str).
    Inputs: subject (str) — typically str(user.id)
    Outputs: str — encoded JWT
    Owner: [Claude]
    """
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_type: str) -> Optional[str]:
    """
    Purpose: Decode and validate a JWT. Returns the subject (user_id) if valid.
    Inputs: token (str), expected_type ('access' | 'refresh')
    Outputs: str — user_id from subject claim, or None if invalid/expired
    Owner: [Claude]
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != expected_type:
            return None
        return payload.get("sub")
    except JWTError:
        return None
