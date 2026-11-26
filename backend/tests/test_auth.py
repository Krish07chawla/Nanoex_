from tests.conftest import admin_login, make_headers, register


def test_register_and_login(client):
    register(client, "Asha")
    reply = client.post("/api/auth/login", json={"email": "asha@test.in", "password": "secret123"})
    assert reply.status_code == 200
    token = reply.json()["token"]
    me = client.get("/api/auth/me", headers=make_headers(token))
    assert me.json()["role"] == "STUDENT"


def test_duplicate_email_is_rejected(client):
    register(client, "Asha")
    reply = client.post(
        "/api/auth/register", json={"name": "Asha", "email": "asha@test.in", "password": "secret123", "role": "STUDENT"}
    )
    assert reply.status_code == 400


def test_wrong_password_is_rejected(client):
    register(client, "Asha")
    reply = client.post("/api/auth/login", json={"email": "asha@test.in", "password": "wrong-password"})
    assert reply.status_code == 401


def test_too_many_wrong_passwords_are_blocked(client):
    register(client, "Asha")
    for _ in range(5):
        client.post("/api/auth/login", json={"email": "asha@test.in", "password": "wrong-password"})
    reply = client.post("/api/auth/login", json={"email": "asha@test.in", "password": "secret123"})
    assert reply.status_code == 429


def test_nobody_can_register_as_admin(client):
    reply = client.post(
        "/api/auth/register", json={"name": "Evil", "email": "evil@test.in", "password": "secret123", "role": "ADMIN"}
    )
    assert reply.status_code == 422


def test_pages_need_login(client):
    assert client.get("/api/portfolio").status_code == 401


def test_student_cannot_use_admin_pages(client):
    student = register(client, "Asha")
    assert client.get("/api/admin/users", headers=student["headers"]).status_code == 403


def test_trader_cannot_trade(client):
    trader = register(client, "Tara", "TRADER")
    order = {"symbol": "TCS", "side": "BUY", "order_type": "MARKET", "quantity": 1}
    assert client.post("/api/orders", json=order, headers=trader["headers"]).status_code == 403


def test_disabled_user_cannot_log_in(client):
    student = register(client, "Asha")
    admin = admin_login(client)
    client.patch(f"/api/admin/users/{student['id']}/active", json={"is_active": False}, headers=admin)
    reply = client.post("/api/auth/login", json={"email": "asha@test.in", "password": "secret123"})
    assert reply.status_code == 403
    # the old token stops working too
    assert client.get("/api/auth/me", headers=student["headers"]).status_code == 401
