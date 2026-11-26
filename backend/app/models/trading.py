"""Tables for trading: orders, holdings, watchlist, price alerts, AI ideas."""

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.core.clock import utcnow
from app.database import Base


class Order(Base):
    """One buy/sell order. A filled order is also the trade record."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(4), nullable=False)  # BUY or SELL
    order_type = Column(String(10), nullable=False)  # MARKET, LIMIT, STOP_LOSS
    quantity = Column(Integer, nullable=False)
    limit_price = Column(Float, nullable=True)  # limit price or stop trigger price
    status = Column(String(10), default="PENDING")
    fill_price = Column(Float, nullable=True)
    charges = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)  # profit made when a SELL is filled
    reject_reason = Column(String(100), default="")
    source = Column(String(10), default="MANUAL")  # MANUAL or AI
    created_at = Column(DateTime, default=utcnow)
    filled_at = Column(DateTime, nullable=True)


class Holding(Base):
    """Shares a user currently owns."""

    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False)
    quantity = Column(Integer, nullable=False)
    avg_price = Column(Float, nullable=False)


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False)


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False)
    direction = Column(String(5), nullable=False)  # ABOVE or BELOW
    price = Column(Float, nullable=False)
    triggered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)


class AiSuggestion(Base):
    """A trade idea made by the AI advisor (or the rule-based backup)."""

    __tablename__ = "ai_suggestions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(4), nullable=False)
    quantity = Column(Integer, nullable=False)
    stop_loss = Column(Float, nullable=True)
    outlook = Column(String(200), default="")
    reason = Column(Text, default="")
    confidence = Column(String(10), default="MEDIUM")
    source = Column(String(10), default="rules")  # "grok" or "rules"
    created_at = Column(DateTime, default=utcnow)
