"""Saves admin actions so they can be checked later."""

from sqlalchemy.orm import Session

from app.models import AuditLog


def log_action(db: Session, actor_id: int, action: str, target_user_id: int | None, detail: str):
    db.add(AuditLog(actor_id=actor_id, action=action, target_user_id=target_user_id, detail=detail))
