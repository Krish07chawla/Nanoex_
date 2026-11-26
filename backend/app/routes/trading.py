"""Orders, portfolio, trade history, wallet and leaderboard (student side)."""

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core import constants as c
from app.core.security import get_current_user, require_roles
from app.database import get_db
from app.models import Order, User
from app.schemas.trading import OrderEdit, OrderIn, order_to_dict
from app.services import admin_service, trading_service, wallet_service
from app.services.trading_service import TradingError

router = APIRouter(tags=["trading"])
student_only = require_roles(c.STUDENT)


@router.post("/orders")
def place_order(data: OrderIn, user: User = Depends(student_only), db: Session = Depends(get_db)):
    try:
        order = trading_service.place_order(db, user, data)
    except TradingError as error:
        raise HTTPException(400, str(error)) from None
    return order_to_dict(order)


@router.get("/orders")
def list_orders(status: str | None = None, user: User = Depends(student_only), db: Session = Depends(get_db)):
    query = db.query(Order).filter_by(user_id=user.id)
    if status:
        query = query.filter_by(status=status.upper())
    return [order_to_dict(o) for o in query.order_by(Order.id.desc()).limit(200).all()]


@router.patch("/orders/{order_id}")
def edit_order(order_id: int, data: OrderEdit, user: User = Depends(student_only), db: Session = Depends(get_db)):
    try:
        order = trading_service.edit_order(db, user, order_id, data.quantity, data.limit_price)
    except TradingError as error:
        raise HTTPException(400, str(error)) from None
    return order_to_dict(order)


@router.delete("/orders/{order_id}")
def cancel_order(order_id: int, user: User = Depends(student_only), db: Session = Depends(get_db)):
    try:
        order = trading_service.cancel_order(db, user, order_id)
    except TradingError as error:
        raise HTTPException(400, str(error)) from None
    return order_to_dict(order)


@router.get("/portfolio")
def portfolio(user: User = Depends(student_only), db: Session = Depends(get_db)):
    return trading_service.get_portfolio(db, user.id)


@router.get("/trades/export")
def export_trades(user: User = Depends(student_only), db: Session = Depends(get_db)):
    """Download filled orders as a CSV file."""
    orders = db.query(Order).filter_by(user_id=user.id, status=c.FILLED).order_by(Order.id).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["time", "symbol", "side", "type", "quantity", "price", "charges", "profit"])
    for o in orders:
        writer.writerow([o.filled_at, o.symbol, o.side, o.order_type, o.quantity, o.fill_price, o.charges, o.realized_pnl])
    return Response(buffer.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=trades.csv"})


@router.get("/wallet")
def wallet(user: User = Depends(student_only), db: Session = Depends(get_db)):
    return {
        "balance": wallet_service.get_wallet(db, user.id).balance,
        "capital": wallet_service.total_capital(db, user.id),
        "transactions": wallet_service.list_transactions(db, user.id),
    }


@router.get("/leaderboard")
def leaderboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return admin_service.leaderboard(db)
