"""Importing every model here makes sure all tables are created."""

from app.models.classroom import (  # noqa: F401
    ClassMember,
    ClassNote,
    ClassQuestion,
    ClassSession,
    PriceTick,
    StudentNote,
)
from app.models.trading import (  # noqa: F401
    AiSuggestion,
    Holding,
    Order,
    PriceAlert,
    WatchlistItem,
)
from app.models.user import AuditLog, User, Wallet, WalletTransaction  # noqa: F401
