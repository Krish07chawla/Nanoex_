"""Stock prices, chart history, watchlist and price alerts."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core import constants as c
from app.core.security import get_current_user, require_roles
from app.database import get_db
from app.market.feed import feed
from app.market.universe import STOCKS
from app.models import PriceAlert, User, WatchlistItem
from app.schemas.trading import AlertIn, SymbolIn

router = APIRouter(tags=["market"])


@router.get("/market/quotes")
def quotes(user: User = Depends(get_current_user)):
    data = feed.snapshot()
    data["stocks"] = [{"symbol": symbol, "name": info["name"]} for symbol, info in STOCKS.items()]
    return data


@router.get("/market/history/{symbol}")
def history(symbol: str, user: User = Depends(get_current_user)):
    symbol = symbol.upper()
    if symbol not in STOCKS:
        raise HTTPException(404, "Unknown stock")
    return {"symbol": symbol, "points": feed.get_history(symbol)}


# ---------- watchlist ----------


@router.get("/watchlist")
def get_watchlist(user: User = Depends(require_roles(c.STUDENT)), db: Session = Depends(get_db)):
    return [item.symbol for item in db.query(WatchlistItem).filter_by(user_id=user.id).all()]


@router.post("/watchlist")
def add_to_watchlist(data: SymbolIn, user: User = Depends(require_roles(c.STUDENT)), db: Session = Depends(get_db)):
    symbol = data.symbol.upper()
    if symbol not in STOCKS:
        raise HTTPException(404, "Unknown stock")
    if not db.query(WatchlistItem).filter_by(user_id=user.id, symbol=symbol).first():
        db.add(WatchlistItem(user_id=user.id, symbol=symbol))
        db.commit()
    return {"ok": True}


@router.delete("/watchlist/{symbol}")
def remove_from_watchlist(symbol: str, user: User = Depends(require_roles(c.STUDENT)), db: Session = Depends(get_db)):
    db.query(WatchlistItem).filter_by(user_id=user.id, symbol=symbol.upper()).delete()
    db.commit()
    return {"ok": True}


# ---------- price alerts ----------


@router.get("/alerts")
def get_alerts(user: User = Depends(require_roles(c.STUDENT)), db: Session = Depends(get_db)):
    alerts = db.query(PriceAlert).filter_by(user_id=user.id).order_by(PriceAlert.id.desc()).all()
    return [
        {"id": a.id, "symbol": a.symbol, "direction": a.direction, "price": a.price, "triggered": a.triggered}
        for a in alerts
    ]


@router.post("/alerts")
def add_alert(data: AlertIn, user: User = Depends(require_roles(c.STUDENT)), db: Session = Depends(get_db)):
    symbol = data.symbol.upper()
    if symbol not in STOCKS:
        raise HTTPException(404, "Unknown stock")
    db.add(PriceAlert(user_id=user.id, symbol=symbol, direction=data.direction, price=data.price))
    db.commit()
    return {"ok": True}


@router.delete("/alerts/{alert_id}")
def delete_alert(alert_id: int, user: User = Depends(require_roles(c.STUDENT)), db: Session = Depends(get_db)):
    db.query(PriceAlert).filter_by(id=alert_id, user_id=user.id).delete()
    db.commit()
    return {"ok": True}
