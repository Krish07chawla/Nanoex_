"""Register, login and "who am I"."""

import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import create_token, get_current_user, hash_password, verify_password
from app.database import get_db
from app.models import User
from app.schemas.auth import LoginIn, RegisterIn, user_to_dict
from app.services import wallet_service

router = APIRouter(prefix="/auth", tags=["auth"])

# Very small protection against password guessing: 5 wrong tries per 5 minutes
failed_logins: dict[str, list[float]] = {}


@router.post("/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(400, "That email is already registered")
    user = User(name=data.name.strip(), email=email, password_hash=hash_password(data.password), role=data.role)
    db.add(user)
    db.flush()
    wallet_service.get_wallet(db, user.id)  # every user gets an empty wallet
    db.commit()
    return {"token": create_token(user), "user": user_to_dict(user)}


@router.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    email = data.email.lower()
    recent = [t for t in failed_logins.get(email, []) if time.time() - t < 300]
    if len(recent) >= 5:
        raise HTTPException(429, "Too many wrong tries. Please wait a few minutes.")

    user = db.query(User).filter_by(email=email).first()
    if user is None or not verify_password(data.password, user.password_hash):
        failed_logins[email] = recent + [time.time()]
        raise HTTPException(401, "Wrong email or password")
    if not user.is_active:
        raise HTTPException(403, "This account is disabled. Please contact the admin.")
    failed_logins.pop(email, None)
    return {"token": create_token(user), "user": user_to_dict(user)}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return user_to_dict(user)
