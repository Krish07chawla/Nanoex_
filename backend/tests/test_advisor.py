import json

from app import config
from app.services import advisor_service, indicators
from tests.conftest import rich_student


def ask(client, student):
    reply = client.post("/api/advisor/suggestions", headers=student["headers"])
    assert reply.status_code == 200, reply.text
    return reply.json()


def test_indicators():
    assert indicators.sma([1, 2, 3, 4], 2) == 3.5
    assert indicators.sma([1], 5) is None
    assert indicators.rsi(list(range(1, 20))) == 100.0  # only rising prices
    assert indicators.describe(list(range(1, 30)))["trend"] == "UP"
    assert indicators.describe(list(range(30, 1, -1)))["trend"] == "DOWN"


def test_rule_based_advisor_works_without_a_key(client):
    student = rich_student(client)
    result = ask(client, student)
    assert result["source"] == "rules"
    assert "No Grok key" in result["note"]
    assert "not financial advice" in result["disclaimer"]
    for idea in result["suggestions"]:
        assert idea["side"] in ("BUY", "SELL") and idea["quantity"] >= 1
    # saved ideas can be read again
    assert len(client.get("/api/advisor/suggestions", headers=student["headers"]).json()) == len(result["suggestions"])


def test_rule_advisor_uses_the_students_own_positions(client):
    from app.market.feed import feed

    student = rich_student(client)
    order = {"symbol": "TCS", "side": "BUY", "order_type": "MARKET", "quantity": 10}
    client.post("/api/orders", json=order, headers=student["headers"])
    feed.set_price("TCS", 3400.0)  # now up more than 6%
    ideas = ask(client, student)["suggestions"]
    tcs = [i for i in ideas if i["symbol"] == "TCS"][0]
    assert tcs["side"] == "SELL" and tcs["quantity"] == 5
    assert "up" in tcs["reason"]


def test_grok_agent_calls_tools_then_answers(client, monkeypatch):
    student = rich_student(client, amount=100000)
    monkeypatch.setattr(config, "XAI_API_KEY", "test-key")
    calls = []

    def fake_grok(messages):
        calls.append(messages)
        if len(calls) == 1:  # first the agent asks for the student's history
            return {"content": None, "tool_calls": [{"id": "1", "function": {"name": "get_trading_summary", "arguments": "{}"}}]}
        if len(calls) == 2:  # then for a stock analysis
            return {"content": None, "tool_calls": [{"id": "2", "function": {"name": "get_stock_analysis", "arguments": '{"symbol": "TCS"}'}}]}
        answer = {
            "insight": "You have not traded yet.",
            "suggestions": [
                {"symbol": "TCS", "side": "BUY", "quantity": 9999, "stop_loss": 3100, "outlook": "Up", "reason": "Trend", "confidence": "HIGH"},
                {"symbol": "FAKE", "side": "BUY", "quantity": 1, "reason": "unknown stock"},
            ],
        }
        return {"content": "Here you go:\n" + json.dumps(answer), "tool_calls": None}

    monkeypatch.setattr(advisor_service, "call_grok", fake_grok)
    result = ask(client, student)

    assert result["source"] == "grok"
    assert result["insight"] == "You have not traded yet."
    # the tool results were sent back to Grok
    assert [m["role"] for m in calls[-1] if m["role"] == "tool"] == ["tool", "tool"]
    # the unknown stock was dropped and 9999 shares were cut to what 100000 cash can buy
    assert len(result["suggestions"]) == 1
    assert result["suggestions"][0]["quantity"] == int(100000 // 3200)


def test_falls_back_to_rules_when_grok_fails(client, monkeypatch):
    student = rich_student(client)
    monkeypatch.setattr(config, "XAI_API_KEY", "test-key")

    def broken_grok(messages):
        raise RuntimeError("network down")

    monkeypatch.setattr(advisor_service, "call_grok", broken_grok)
    result = ask(client, student)
    assert result["source"] == "rules"
    assert "RuntimeError" in result["note"]


def test_bad_ideas_are_dropped(client):
    held = {"TCS": 2}
    assert advisor_service.clean_suggestion({"symbol": "TCS", "side": "SELL", "quantity": 50}, 0, held)["quantity"] == 2
    assert advisor_service.clean_suggestion({"symbol": "INFY", "side": "SELL", "quantity": 1}, 0, held) is None
    assert advisor_service.clean_suggestion({"symbol": "TCS", "side": "BUY", "quantity": 1}, 100, held) is None
    assert advisor_service.clean_suggestion({"symbol": "TCS", "side": "HOLD", "quantity": 1}, 99999, held) is None
