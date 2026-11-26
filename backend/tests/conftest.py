"""Shared test setup. Tests use a temporary database and never touch the internet."""

import os
import tempfile

# These must be set BEFORE the app is imported.
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["START_FEED"] = "false"
os.environ["MARKET_PROVIDER"] = "demo"
os.environ["XAI_API_KEY"] = ""
os.environ["ADMIN_EMAIL"] = "admin@test.in"
os.environ["ADMIN_PASSWORD"] = "AdminPass1"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.market.feed import feed  # noqa: E402
from app.market.universe import STOCKS  # noqa: E402
from app.routes import auth  # noqa: E402


@pytest.fixture()
def client():
    """A fresh empty database and fixed prices for every test."""
    Base.metadata.drop_all(engine)
    auth.failed_logins.clear()
    with TestClient(app) as test_client:  # starting the app creates tables + admin
        for symbol, info in STOCKS.items():
            feed.set_price(symbol, info["base"])
        yield test_client


def make_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def register(client, name: str, role: str = "STUDENT") -> dict:
    """Register a user and return {"headers": ..., "id": ...}."""
    email = f"{name.lower()}@test.in"
    reply = client.post("/api/auth/register", json={"name": name, "email": email, "password": "secret123", "role": role})
    assert reply.status_code == 200, reply.text
    return {"headers": make_headers(reply.json()["token"]), "id": reply.json()["user"]["id"]}


def admin_login(client) -> dict:
    reply = client.post("/api/auth/login", json={"email": "admin@test.in", "password": "AdminPass1"})
    return make_headers(reply.json()["token"])


def give_money(client, student_id: int, amount: float = 100000):
    reply = client.post(
        "/api/admin/wallet", json={"kind": "CREDIT", "amount": amount, "user_ids": [student_id]}, headers=admin_login(client)
    )
    assert reply.status_code == 200, reply.text


def rich_student(client, name: str = "Asha", amount: float = 100000) -> dict:
    """A student who already received virtual money."""
    student = register(client, name)
    give_money(client, student["id"], amount)
    return student
