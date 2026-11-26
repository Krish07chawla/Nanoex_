"""Passwords, login tokens and "who is calling?" checks."""

from datetime import timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app import config
from app.core.clock import utcnow
from app.database import get_db
from app.models import User

bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "exp": utcnow() + timedelta(hours=config.JWT_HOURS),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")


def read_token(token: str) -> int | None:
    """Return the user id inside a token, or None if the token is bad/expired."""
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    """Used by routes that need a logged-in user."""
    if credentials is None:
        raise HTTPException(401, "Please log in")
    user_id = read_token(credentials.credentials)
    user = db.get(User, user_id) if user_id else None
    if user is None or not user.is_active:
        raise HTTPException(401, "Please log in again")
    return user


def require_roles(*roles: str):
    """Make a dependency that only lets the given roles in."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "You are not allowed to do this")
        return user

    return checker
