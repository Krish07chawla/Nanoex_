from app.database import SessionLocal
from app.market.feed import feed
from app.services import trading_service
from tests.conftest import rich_student

TCS_PRICE = 3200.0


def order(client, student, side="BUY", qty=1, order_type="MARKET", price=None, symbol="TCS"):
    body = {"symbol": symbol, "side": side, "order_type": order_type, "quantity": qty, "limit_price": price}
    return client.post("/api/orders", json=body, headers=student["headers"])


def portfolio(client, student):
    return client.get("/api/portfolio", headers=student["headers"]).json()


def test_market_buy_uses_cash_and_adds_holding(client):
    student = rich_student(client)
    reply = order(client, student, qty=10)
    assert reply.status_code == 200
    assert reply.json()["status"] == "FILLED"
    # 10 x 3200 = 32000, brokerage is 0.03% but at most Rs 20
    assert reply.json()["charges"] == 9.6
    data = portfolio(client, student)
    assert data["cash"] == round(100000 - 32000 - 9.6, 2)
    assert data["holdings"][0]["quantity"] == 10


def test_sell_makes_profit_and_removes_holding(client):
    student = rich_student(client)
    order(client, student, qty=10)
    feed.set_price("TCS", 3300.0)
    reply = order(client, student, side="SELL", qty=10)
    # profit = (3300 - 3200) x 10 - brokerage on the sell (9.9)
    assert reply.json()["realized_pnl"] == 990.1
    data = portfolio(client, student)
    assert data["holdings"] == []
    assert data["realized_pnl"] == 990.1


def test_cannot_buy_without_enough_cash(client):
    student = rich_student(client, amount=1000)
    reply = order(client, student, qty=10)
    assert reply.status_code == 400
    assert "cash" in reply.json()["detail"]
    assert client.get("/api/orders", headers=student["headers"]).json() == []  # nothing saved


def test_cannot_sell_shares_you_do_not_own(client):
    student = rich_student(client)
    assert order(client, student, side="SELL", qty=1).status_code == 400


def test_stop_loss_is_only_for_selling(client):
    student = rich_student(client)
    assert order(client, student, order_type="STOP_LOSS", price=3000).status_code == 400


def test_limit_buy_waits_then_fills_when_price_drops(client):
    student = rich_student(client)
    reply = order(client, student, qty=5, order_type="LIMIT", price=3100)
    assert reply.json()["status"] == "PENDING"

    with SessionLocal() as db:  # price is still 3200, nothing happens
        trading_service.process_pending_orders(db, {"TCS": {"price": 3200.0}})
    assert client.get("/api/orders?status=PENDING", headers=student["headers"]).json() != []

    with SessionLocal() as db:  # price drops to 3090, order fills at 3090
        events = trading_service.process_pending_orders(db, {"TCS": {"price": 3090.0}})
    assert len(events) == 1
    filled = client.get("/api/orders?status=FILLED", headers=student["headers"]).json()
    assert filled[0]["fill_price"] == 3090.0


def test_stop_loss_sells_when_price_falls(client):
    student = rich_student(client)
    order(client, student, qty=2)
    order(client, student, side="SELL", qty=2, order_type="STOP_LOSS", price=3000)
    with SessionLocal() as db:
        trading_service.process_pending_orders(db, {"TCS": {"price": 2990.0}})
    assert portfolio(client, student)["holdings"] == []


def test_cancel_and_edit_waiting_order(client):
    student = rich_student(client)
    waiting = order(client, student, qty=5, order_type="LIMIT", price=3000).json()
    edited = client.patch(f"/api/orders/{waiting['id']}", json={"limit_price": 3050}, headers=student["headers"])
    assert edited.json()["limit_price"] == 3050
    cancelled = client.delete(f"/api/orders/{waiting['id']}", headers=student["headers"])
    assert cancelled.json()["status"] == "CANCELLED"
    # a cancelled order cannot be cancelled again
    assert client.delete(f"/api/orders/{waiting['id']}", headers=student["headers"]).status_code == 400


def test_average_price_when_buying_twice(client):
    student = rich_student(client)
    order(client, student, qty=10)
    feed.set_price("TCS", 3400.0)
    order(client, student, qty=10)
    assert portfolio(client, student)["holdings"][0]["avg_price"] == 3300.0


def test_portfolio_profit_uses_live_price(client):
    student = rich_student(client)
    order(client, student, qty=10)
    feed.set_price("TCS", 3250.0)
    data = portfolio(client, student)
    assert data["holdings"][0]["pnl"] == 500.0
    assert data["capital"] == 100000


def test_trade_export_is_csv(client):
    student = rich_student(client)
    order(client, student, qty=1)
    reply = client.get("/api/trades/export", headers=student["headers"])
    assert reply.headers["content-type"].startswith("text/csv")
    assert "TCS" in reply.text


def test_leaderboard_ranks_by_return(client):
    winner = rich_student(client, "Asha")
    loser = rich_student(client, "Ravi")
    order(client, winner, qty=10)
    order(client, loser, qty=10)
    feed.set_price("TCS", 3000.0)
    order(client, loser, side="SELL", qty=10)  # Ravi sells at a loss
    feed.set_price("TCS", 3400.0)  # Asha is still holding and gains
    board = client.get("/api/leaderboard", headers=winner["headers"]).json()
    assert [row["name"] for row in board] == ["Asha", "Ravi"]


def test_watchlist_and_alerts(client):
    student = rich_student(client)
    client.post("/api/watchlist", json={"symbol": "tcs"}, headers=student["headers"])
    assert client.get("/api/watchlist", headers=student["headers"]).json() == ["TCS"]
    client.post("/api/alerts", json={"symbol": "TCS", "direction": "ABOVE", "price": 3300}, headers=student["headers"])
    from app.services import alert_service

    with SessionLocal() as db:
        events = alert_service.check_alerts(db, {"TCS": {"price": 3310.0}})
    assert len(events) == 1
    assert client.get("/api/alerts", headers=student["headers"]).json()[0]["triggered"] is True
