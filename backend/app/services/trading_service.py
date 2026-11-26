"""Trading: place, fill, change and cancel orders, and build the portfolio."""

from sqlalchemy.orm import Session

from app import config
from app.core import constants as c
from app.core.clock import utcnow
from app.market.feed import feed
from app.market.universe import STOCKS
from app.models import Holding, Order, User
from app.services.wallet_service import change_balance, get_wallet, total_capital


class TradingError(Exception):
    """A normal "you cannot do that" problem. The message is shown to the user."""


# ---------- small helpers ----------


def calc_charges(trade_value: float) -> float:
    """Brokerage: 0.03% of the trade value, at most Rs 20."""
    return round(min(trade_value * config.BROKERAGE_RATE, config.BROKERAGE_MAX), 2)


def get_holding(db: Session, user_id: int, symbol: str) -> Holding | None:
    return db.query(Holding).filter_by(user_id=user_id, symbol=symbol).first()


def should_fill(order: Order, price: float) -> bool:
    """Is the live price good enough to fill this order now?"""
    if order.order_type == c.MARKET:
        return True
    if order.order_type == c.LIMIT:
        if order.side == c.BUY:
            return price <= order.limit_price  # buy at the limit price or cheaper
        return price >= order.limit_price  # sell at the limit price or higher
    # STOP_LOSS is a sell order that fires when the price falls to the trigger
    return price <= order.limit_price


# ---------- filling ----------


def fill_order(db: Session, order: Order, price: float):
    """Complete an order at the given price. Raises TradingError if impossible."""
    value = round(price * order.quantity, 2)
    charges = calc_charges(value)

    if order.side == c.BUY:
        note = f"Bought {order.quantity} {order.symbol} @ {price}"
        try:
            change_balance(db, order.user_id, -(value + charges), c.TRADE_BUY, note)
        except ValueError:
            raise TradingError("Not enough virtual cash") from None
        holding = get_holding(db, order.user_id, order.symbol)
        if holding:
            new_qty = holding.quantity + order.quantity
            holding.avg_price = round((holding.avg_price * holding.quantity + value) / new_qty, 2)
            holding.quantity = new_qty
        else:
            db.add(Holding(user_id=order.user_id, symbol=order.symbol, quantity=order.quantity, avg_price=price))
        order.realized_pnl = 0.0
    else:
        holding = get_holding(db, order.user_id, order.symbol)
        if holding is None or holding.quantity < order.quantity:
            raise TradingError("Not enough shares to sell")
        order.realized_pnl = round((price - holding.avg_price) * order.quantity - charges, 2)
        note = f"Sold {order.quantity} {order.symbol} @ {price}"
        change_balance(db, order.user_id, value - charges, c.TRADE_SELL, note)
        holding.quantity -= order.quantity
        if holding.quantity == 0:
            db.delete(holding)

    order.status = c.FILLED
    order.fill_price = price
    order.charges = charges
    order.filled_at = utcnow()


# ---------- placing and changing orders ----------


def place_order(db: Session, user: User, data) -> Order:
    """Create an order. Market orders fill at once, others may wait."""
    if data.symbol not in STOCKS:
        raise TradingError("Unknown stock")
    if data.order_type in (c.LIMIT, c.STOP_LOSS) and not data.limit_price:
        raise TradingError("Please enter a price for this order type")
    if data.order_type == c.STOP_LOSS and data.side != c.SELL:
        raise TradingError("Stop-loss orders are only for selling")
    price = feed.price(data.symbol)
    if price is None:
        raise TradingError("Live price is not ready yet, try again in a few seconds")

    if data.side == c.SELL:
        holding = get_holding(db, user.id, data.symbol)
        if holding is None or holding.quantity < data.quantity:
            raise TradingError("You do not own that many shares")
    elif data.order_type == c.LIMIT:
        # Early warning only. Cash is checked again when the order fills.
        needed = data.quantity * data.limit_price
        if get_wallet(db, user.id).balance < needed:
            raise TradingError("Not enough virtual cash for this order")

    order = Order(
        user_id=user.id,
        symbol=data.symbol,
        side=data.side,
        order_type=data.order_type,
        quantity=data.quantity,
        limit_price=data.limit_price,
        source=data.source,
        status=c.PENDING,
    )
    db.add(order)
    try:
        if should_fill(order, price):
            fill_order(db, order, price)
    except TradingError:
        db.rollback()
        raise
    db.commit()
    return order


def cancel_order(db: Session, user: User, order_id: int) -> Order:
    order = db.get(Order, order_id)
    if order is None or order.user_id != user.id:
        raise TradingError("Order not found")
    if order.status != c.PENDING:
        raise TradingError("Only waiting orders can be cancelled")
    order.status = c.CANCELLED
    db.commit()
    return order


def edit_order(db: Session, user: User, order_id: int, quantity: int | None, limit_price: float | None) -> Order:
    order = db.get(Order, order_id)
    if order is None or order.user_id != user.id:
        raise TradingError("Order not found")
    if order.status != c.PENDING:
        raise TradingError("Only waiting orders can be changed")
    if quantity:
        order.quantity = quantity
    if limit_price:
        order.limit_price = limit_price
    db.commit()
    return order


def process_pending_orders(db: Session, prices: dict) -> list[dict]:
    """Called on every price update. Fills waiting orders whose price is reached."""
    events = []
    waiting = db.query(Order).filter_by(status=c.PENDING).all()
    for order in waiting:
        quote = prices.get(order.symbol)
        if quote is None or not should_fill(order, quote["price"]):
            continue
        try:
            fill_order(db, order, quote["price"])
            message = f"{order.order_type} {order.side} of {order.quantity} {order.symbol} filled at Rs {quote['price']}"
        except TradingError as error:
            order.status = c.REJECTED
            order.reject_reason = str(error)
            message = f"{order.order_type} {order.side} of {order.symbol} was rejected: {error}"
        events.append({"type": "order", "user_id": order.user_id, "message": message})
    db.commit()
    return events


# ---------- portfolio ----------


def get_portfolio(db: Session, user_id: int) -> dict:
    """Cash, holdings with live value and profit, and totals."""
    cash = get_wallet(db, user_id).balance
    rows = []
    holdings_value = 0.0
    invested = 0.0
    for holding in db.query(Holding).filter_by(user_id=user_id).all():
        price = feed.price(holding.symbol) or holding.avg_price
        value = round(price * holding.quantity, 2)
        cost = round(holding.avg_price * holding.quantity, 2)
        rows.append(
            {
                "symbol": holding.symbol,
                "name": STOCKS[holding.symbol]["name"],
                "quantity": holding.quantity,
                "avg_price": holding.avg_price,
                "price": price,
                "value": value,
                "pnl": round(value - cost, 2),
                "pnl_pct": round((value - cost) / cost * 100, 2) if cost else 0.0,
            }
        )
        holdings_value += value
        invested += cost

    capital = total_capital(db, user_id)
    total_value = round(cash + holdings_value, 2)
    realized = (
        db.query(Order).filter_by(user_id=user_id, status=c.FILLED, side=c.SELL).with_entities(Order.realized_pnl).all()
    )
    return {
        "cash": round(cash, 2),
        "holdings_value": round(holdings_value, 2),
        "invested": round(invested, 2),
        "total_value": total_value,
        "capital": capital,
        "total_pnl": round(total_value - capital, 2),
        "total_pnl_pct": round((total_value - capital) / capital * 100, 2) if capital else 0.0,
        "realized_pnl": round(sum(r[0] or 0 for r in realized), 2),
        "holdings": rows,
    }


def get_trade_summary(db: Session, user_id: int) -> dict:
    """Short facts about the student's past trades (used by the AI advisor)."""
    sells = db.query(Order).filter_by(user_id=user_id, status=c.FILLED, side=c.SELL).all()
    wins = [o for o in sells if o.realized_pnl > 0]
    losses = [o for o in sells if o.realized_pnl <= 0]
    all_orders = db.query(Order).filter_by(user_id=user_id, status=c.FILLED).all()
    counts = {}
    for order in all_orders:
        counts[order.symbol] = counts.get(order.symbol, 0) + 1
    return {
        "total_trades": len(all_orders),
        "closed_trades": len(sells),
        "wins": len(wins),
        "losses": len(losses),
        "average_win": round(sum(o.realized_pnl for o in wins) / len(wins), 2) if wins else 0.0,
        "average_loss": round(sum(o.realized_pnl for o in losses) / len(losses), 2) if losses else 0.0,
        "most_traded": sorted(counts, key=counts.get, reverse=True)[:3],
    }
