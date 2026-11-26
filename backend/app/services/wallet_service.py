"""Virtual money: the one place where wallet balances change."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core import constants as c
from app.models import Wallet, WalletTransaction


def get_wallet(db: Session, user_id: int) -> Wallet:
    wallet = db.query(Wallet).filter_by(user_id=user_id).first()
    if wallet is None:
        wallet = Wallet(user_id=user_id, balance=0.0)
        db.add(wallet)
        db.flush()
    return wallet


def change_balance(
    db: Session, user_id: int, amount: float, kind: str, note: str = "", created_by_id: int | None = None
) -> WalletTransaction:
    """Add (+) or remove (-) money and write a ledger line.

    Raises ValueError when the wallet would go below zero.
    """
    wallet = get_wallet(db, user_id)
    new_balance = round(wallet.balance + amount, 2)
    if new_balance < 0:
        raise ValueError("Not enough virtual cash")
    wallet.balance = new_balance
    transaction = WalletTransaction(
        user_id=user_id,
        kind=kind,
        amount=round(amount, 2),
        balance_after=new_balance,
        note=note,
        created_by_id=created_by_id,
    )
    db.add(transaction)
    return transaction


def total_capital(db: Session, user_id: int) -> float:
    """All money the admin gave (minus what the admin took back)."""
    total = (
        db.query(func.sum(WalletTransaction.amount))
        .filter(
            WalletTransaction.user_id == user_id,
            WalletTransaction.kind.in_([c.ADMIN_CREDIT, c.ADMIN_DEBIT]),
        )
        .scalar()
    )
    return round(total or 0.0, 2)


def list_transactions(db: Session, user_id: int, limit: int = 100) -> list[dict]:
    rows = (
        db.query(WalletTransaction)
        .filter_by(user_id=user_id)
        .order_by(WalletTransaction.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": t.id,
            "kind": t.kind,
            "amount": t.amount,
            "balance_after": t.balance_after,
            "note": t.note,
            "created_at": t.created_at.isoformat() + "Z",
        }
        for t in rows
    ]
