"""Admin pages: see every account and send virtual money."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core import constants as c
from app.core.security import require_roles
from app.database import get_db
from app.models import AuditLog, Order, User
from app.schemas.admin import ActiveIn, MoneyIn
from app.schemas.trading import order_to_dict
from app.services import admin_service, audit_service, trading_service, wallet_service
from app.services.admin_service import AdminError

router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = require_roles(c.ADMIN)


@router.get("/users")
def list_users(role: str | None = None, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    query = db.query(User)
    if role:
        query = query.filter_by(role=role.upper())
    return [admin_service.user_overview(db, u) for u in query.order_by(User.id).all()]


@router.get("/users/{user_id}")
def user_detail(user_id: int, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    detail = {"user": admin_service.user_overview(db, user)}
    if user.role == c.STUDENT:
        detail["portfolio"] = trading_service.get_portfolio(db, user.id)
        orders = db.query(Order).filter_by(user_id=user.id).order_by(Order.id.desc()).limit(50).all()
        detail["orders"] = [order_to_dict(o) for o in orders]
        detail["transactions"] = wallet_service.list_transactions(db, user.id, 50)
    return detail


@router.post("/wallet")
def send_money(data: MoneyIn, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    try:
        count = admin_service.move_money(db, admin, data)
    except AdminError as error:
        raise HTTPException(400, str(error)) from None
    return {"students": count}


@router.patch("/users/{user_id}/active")
def set_active(user_id: int, data: ActiveIn, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    if user.id == admin.id:
        raise HTTPException(400, "You cannot disable your own account")
    user.is_active = data.is_active
    audit_service.log_action(db, admin.id, "SET_ACTIVE", user.id, f"{user.email} active={data.is_active}")
    db.commit()
    return {"ok": True}


@router.get("/audit")
def audit_log(admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(200).all()
    return [
        {
            "id": r.id, "action": r.action, "actor_id": r.actor_id, "target_user_id": r.target_user_id,
            "detail": r.detail, "created_at": r.created_at.isoformat() + "Z",
        }
        for r in rows
    ]
