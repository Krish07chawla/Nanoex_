"""Tables for users, their virtual wallet and the admin audit log."""

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String

from app.core.clock import utcnow
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(10), nullable=False)  # ADMIN, TRADER or STUDENT
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)


class Wallet(Base):
    """Each user has one wallet holding virtual rupees."""

    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    balance = Column(Float, default=0.0)


class WalletTransaction(Base):
    """The ledger: every change to a wallet is saved here."""

    __tablename__ = "wallet_transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    kind = Column(String(20), nullable=False)  # ADMIN_CREDIT, TRADE_BUY ...
    amount = Column(Float, nullable=False)  # + adds money, - removes money
    balance_after = Column(Float, nullable=False)
    note = Column(String(200), default="")
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow)


class AuditLog(Base):
    """Records important admin actions (who did what, to whom)."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)
    target_user_id = Column(Integer, nullable=True)
    detail = Column(String(300), default="")
    created_at = Column(DateTime, default=utcnow)
