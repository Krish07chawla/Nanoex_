"""Price alerts: "tell me when TCS goes above 3300"."""

from sqlalchemy.orm import Session

from app.models import PriceAlert


def check_alerts(db: Session, prices: dict) -> list[dict]:
    """Called on every price update. Returns messages for alerts that fired."""
    events = []
    for alert in db.query(PriceAlert).filter_by(triggered=False).all():
        quote = prices.get(alert.symbol)
        if quote is None:
            continue
        price = quote["price"]
        hit = price >= alert.price if alert.direction == "ABOVE" else price <= alert.price
        if hit:
            alert.triggered = True
            word = "above" if alert.direction == "ABOVE" else "below"
            events.append(
                {
                    "type": "alert",
                    "user_id": alert.user_id,
                    "message": f"{alert.symbol} is {word} Rs {alert.price} (now Rs {price})",
                }
            )
    db.commit()
    return events
