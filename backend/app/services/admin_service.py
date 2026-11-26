"""Admin tools: send or take back virtual money, and overview of accounts."""

from sqlalchemy.orm import Session

from app.core import constants as c
from app.models import User
from app.services import audit_service, trading_service
from app.services.wallet_service import change_balance


class AdminError(Exception):
    """A normal "you cannot do that" problem. The message is shown to the user."""


def move_money(db: Session, admin: User, data) -> int:
    """Credit or debit virtual money for chosen students. Returns how many students."""
    if data.all_students:
        students = db.query(User).filter_by(role=c.STUDENT, is_active=True).all()
    else:
        students = db.query(User).filter(User.id.in_(data.user_ids), User.role == c.STUDENT).all()
    if not students:
        raise AdminError("No students selected")

    sign = 1 if data.kind == "CREDIT" else -1
    kind = c.ADMIN_CREDIT if data.kind == "CREDIT" else c.ADMIN_DEBIT
    try:
        for student in students:
            change_balance(db, student.id, sign * data.amount, kind, data.note or kind.title(), admin.id)
            audit_service.log_action(
                db, admin.id, kind, student.id, f"{data.kind} Rs {data.amount} for {student.email}. {data.note}"
            )
    except ValueError:
        db.rollback()
        raise AdminError(f"{student.name} does not have enough cash to take back") from None
    db.commit()
    return len(students)


def user_overview(db: Session, user: User) -> dict:
    """One row for the admin users table."""
    row = {"id": user.id, "name": user.name, "email": user.email, "role": user.role, "is_active": user.is_active}
    if user.role == c.STUDENT:
        portfolio = trading_service.get_portfolio(db, user.id)
        row.update(
            cash=portfolio["cash"],
            holdings_value=portfolio["holdings_value"],
            total_value=portfolio["total_value"],
            capital=portfolio["capital"],
            total_pnl=portfolio["total_pnl"],
        )
    return row


def leaderboard(db: Session) -> list[dict]:
    """Students ranked by percentage return on the money they were given."""
    rows = []
    for student in db.query(User).filter_by(role=c.STUDENT, is_active=True).all():
        portfolio = trading_service.get_portfolio(db, student.id)
        if portfolio["capital"] > 0:
            rows.append(
                {"name": student.name, "total_value": portfolio["total_value"], "return_pct": portfolio["total_pnl_pct"]}
            )
    rows.sort(key=lambda row: -row["return_pct"])
    for position, row in enumerate(rows, start=1):
        row["rank"] = position
    return rows
