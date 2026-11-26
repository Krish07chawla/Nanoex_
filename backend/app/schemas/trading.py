"""Shapes of data for orders, watchlist and alerts."""

from typing import Literal

from pydantic import BaseModel, Field


class OrderIn(BaseModel):
    symbol: str
    side: Literal["BUY", "SELL"]
    order_type: Literal["MARKET", "LIMIT", "STOP_LOSS"] = "MARKET"
    quantity: int = Field(gt=0, le=100000)
    limit_price: float | None = Field(default=None, gt=0)  # limit or stop price
    source: Literal["MANUAL", "AI"] = "MANUAL"


class OrderEdit(BaseModel):
    quantity: int | None = Field(default=None, gt=0, le=100000)
    limit_price: float | None = Field(default=None, gt=0)


class SymbolIn(BaseModel):
    symbol: str


class AlertIn(BaseModel):
    symbol: str
    direction: Literal["ABOVE", "BELOW"]
    price: float = Field(gt=0)


def order_to_dict(order) -> dict:
    return {
        "id": order.id,
        "symbol": order.symbol,
        "side": order.side,
        "order_type": order.order_type,
        "quantity": order.quantity,
        "limit_price": order.limit_price,
        "status": order.status,
        "fill_price": order.fill_price,
        "charges": order.charges,
        "realized_pnl": order.realized_pnl,
        "reject_reason": order.reject_reason,
        "source": order.source,
        "created_at": order.created_at.isoformat() + "Z",
        "filled_at": order.filled_at.isoformat() + "Z" if order.filled_at else None,
    }
