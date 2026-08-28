"""
Authentication service — JWT token creation and validation.
"""
import jwt
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

from backend.config import JWT_SECRET, JWT_ALGORITHM
from backend.database import SessionLocal
from backend.models import User


@dataclass
class UserContext:
    """Represents an authenticated user's context."""
    user_id: str
    email: str
    department: str
    roles: list[str]


def create_token(user_id: str) -> str:
    """Create a JWT token for the given user."""
    payload = {
        "sub": user_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> str:
    """Decode a JWT token and return the user_id."""
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    return payload["sub"]


def get_user_context(user_id: str) -> UserContext | None:
    """Look up user in DB and return their context."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return None
        return UserContext(
            user_id=user.user_id,
            email=user.email,
            department=user.department,
            roles=user.role_names(),
        )
    finally:
        db.close()


def authenticate(token: str) -> UserContext | None:
    """Validate token and return user context."""
    try:
        user_id = decode_token(token)
        return get_user_context(user_id)
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
