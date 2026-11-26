"""The AI trade advisor.

Main idea: Grok works as an "agent". It does not guess from nothing; it calls
small tools (our own functions below) to read the student's history, portfolio
and market data, and then answers with trade ideas in JSON.

If there is no API key, or Grok fails, a simple rule-based advisor is used
instead, so the feature always works. All ideas are for learning only.
"""

import json
import logging

import httpx
from sqlalchemy.orm import Session

from app import config
from app.core import constants as c
from app.market.feed import feed
from app.market.universe import STOCKS
from app.models import AiSuggestion, User
from app.services import indicators, trading_service

log = logging.getLogger("advisor")

MAX_STEPS = 6  # Grok may call tools at most this many times

SYSTEM_PROMPT = """You are a friendly trading tutor for students who trade with VIRTUAL money on Indian NSE stocks.
First use the tools to read the student's trading summary, portfolio and the stocks.
Then suggest 3 or 4 trades. Rules:
- Only use these stocks: {symbols}.
- Never suggest more shares than the student can afford (BUY) or owns (SELL).
- Explain in simple words and mention a cautious short-term outlook (not a promise).
- Use the student's own history to give one useful habit tip.
Reply with JSON only, no other text, in exactly this shape:
{{"insight": "one sentence about the student's habits",
 "suggestions": [{{"symbol": "TCS", "side": "BUY", "quantity": 5, "stop_loss": 3100.0,
 "outlook": "short outlook", "reason": "simple reason", "confidence": "LOW or MEDIUM or HIGH"}}]}}"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_trading_summary",
            "description": "Wins, losses, average win/loss and most traded stocks of the student.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_portfolio",
            "description": "The student's cash and current holdings with profit/loss.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_analysis",
            "description": "Live price, trend (UP/DOWN/SIDEWAYS) and RSI for one stock.",
            "parameters": {
                "type": "object",
                "properties": {"symbol": {"type": "string"}},
                "required": ["symbol"],
            },
        },
    },
]


class AdvisorError(Exception):
    """Grok could not give a usable answer."""


# ---------- tools that Grok can call ----------


def analyse_stock(symbol: str) -> dict:
    """Price plus indicators for one stock."""
    if symbol not in STOCKS:
        return {"error": f"Unknown stock {symbol}"}
    closes = [point["price"] for point in feed.get_history(symbol)]
    quote = feed.latest.get(symbol, {})
    result = {"symbol": symbol, "price": quote.get("price"), "prev_close": quote.get("prev_close")}
    result.update(indicators.describe(closes))
    return result


def run_tool(db: Session, user: User, name: str, arguments: dict) -> dict:
    if name == "get_trading_summary":
        return trading_service.get_trade_summary(db, user.id)
    if name == "get_portfolio":
        portfolio = trading_service.get_portfolio(db, user.id)
        return {"cash": portfolio["cash"], "holdings": portfolio["holdings"], "total_pnl": portfolio["total_pnl"]}
    if name == "get_stock_analysis":
        return analyse_stock(str(arguments.get("symbol", "")).upper())
    return {"error": f"Unknown tool {name}"}


# ---------- talking to Grok ----------


def call_grok(messages: list[dict]) -> dict:
    """One request to the Grok API. Returns the assistant message."""
    response = httpx.post(
        f"{config.XAI_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {config.XAI_API_KEY}"},
        json={"model": config.XAI_MODEL, "messages": messages, "tools": TOOLS, "tool_choice": "auto"},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]


def parse_json(text: str) -> dict:
    """Grok sometimes wraps JSON in extra text. Take the part between { and }."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise AdvisorError("Grok did not return JSON")
    return json.loads(text[start : end + 1])


def ask_grok(db: Session, user: User) -> dict:
    """The agent loop: let Grok use tools until it gives its final answer."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(symbols=", ".join(STOCKS))},
        {"role": "user", "content": "Please suggest trades for me."},
    ]
    for _ in range(MAX_STEPS):
        reply = call_grok(messages)
        tool_calls = reply.get("tool_calls")
        if not tool_calls:
            return parse_json(reply.get("content") or "")
        messages.append({"role": "assistant", "content": reply.get("content"), "tool_calls": tool_calls})
        for call in tool_calls:
            arguments = json.loads(call["function"].get("arguments") or "{}")
            result = run_tool(db, user, call["function"]["name"], arguments)
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result)})
    raise AdvisorError("Grok used too many steps")


# ---------- checking what Grok says ----------


def clean_suggestion(raw: dict, cash: float, held: dict) -> dict | None:
    """Keep only safe, sensible ideas. Returns None to drop a bad one."""
    symbol = str(raw.get("symbol", "")).upper()
    side = str(raw.get("side", "")).upper()
    price = feed.price(symbol)
    if symbol not in STOCKS or side not in (c.BUY, c.SELL) or not price:
        return None
    try:
        quantity = int(raw.get("quantity", 0))
    except (TypeError, ValueError):
        return None
    quantity = min(quantity, int(cash // price)) if side == c.BUY else min(quantity, held.get(symbol, 0))
    if quantity < 1:
        return None
    try:
        stop_loss = float(raw["stop_loss"]) if raw.get("stop_loss") else None
    except (TypeError, ValueError):
        stop_loss = None
    if side == c.SELL or (stop_loss is not None and stop_loss >= price):
        stop_loss = None
    confidence = str(raw.get("confidence", "MEDIUM")).upper()
    return {
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "stop_loss": stop_loss,
        "outlook": str(raw.get("outlook", ""))[:200],
        "reason": str(raw.get("reason", ""))[:600],
        "confidence": confidence if confidence in ("LOW", "MEDIUM", "HIGH") else "MEDIUM",
    }


# ---------- the simple backup advisor ----------


def habit_insight(summary: dict) -> str:
    if summary["closed_trades"] == 0:
        return "You have no closed trades yet, so these ideas use market trends only."
    text = (
        f"You closed {summary['closed_trades']} trades: {summary['wins']} wins and {summary['losses']} losses "
        f"(average win Rs {summary['average_win']}, average loss Rs {summary['average_loss']})."
    )
    if summary["losses"] and abs(summary["average_loss"]) > summary["average_win"]:
        text += " Your losses are bigger than your wins, so try using stop-loss orders."
    return text


def rule_based(db: Session, user: User) -> dict:
    portfolio = trading_service.get_portfolio(db, user.id)
    cash = portfolio["cash"]
    held = {h["symbol"]: h["quantity"] for h in portfolio["holdings"]}
    profit_pct = {h["symbol"]: h["pnl_pct"] for h in portfolio["holdings"]}  # the student's own positions
    ideas = []
    momentum = []  # used only if there is no clear signal
    for symbol in STOCKS:
        info = analyse_stock(symbol)
        price = info.get("price")
        if not price:
            continue
        score = {"UP": 1, "DOWN": -1}.get(info["trend"], 0)
        if info["rsi"] is not None:
            score += 1 if info["rsi"] < 30 else -1 if info["rsi"] > 70 else 0
        outlook = f"Trend is {info['trend'].lower()}, RSI is {info['rsi']}."
        if symbol in held and profit_pct[symbol] >= 3:
            ideas.append((2, symbol, c.SELL, max(1, held[symbol] // 2), None, outlook,
                          f"You are up {profit_pct[symbol]}% on this stock. Booking part of the profit is a good habit."))
        elif symbol in held and profit_pct[symbol] <= -3:
            ideas.append((2, symbol, c.SELL, max(1, held[symbol] // 2), None, outlook,
                          f"You are down {abs(profit_pct[symbol])}% on this stock. Cutting part of the loss keeps it small."))
        elif score >= 1 and cash >= price:
            quantity = max(1, int(cash * 0.1 // price))
            ideas.append((score, symbol, c.BUY, quantity, round(price * 0.97, 2), outlook, "Price trend is rising."))
        elif score <= -1 and symbol in held:
            quantity = max(1, held[symbol] // 2)
            ideas.append((-score, symbol, c.SELL, quantity, None, outlook, "Price trend is weak, consider taking profit or cutting loss."))
        if info["sma5"] and info["sma20"] and cash >= price:
            momentum.append((info["sma5"] / info["sma20"], symbol, price, outlook))

    if not ideas and momentum:  # no clear signal: offer two small, low-confidence practice ideas
        for _, symbol, price, outlook in sorted(momentum, reverse=True)[:2]:
            quantity = max(1, int(cash * 0.05 // price))
            ideas.append((0, symbol, c.BUY, quantity, round(price * 0.97, 2), outlook,
                          "No strong signal today. This is a small practice idea from the strongest short-term momentum."))
    ideas.sort(key=lambda idea: -idea[0])
    suggestions = [
        {
            "symbol": s, "side": side, "quantity": q, "stop_loss": stop, "outlook": outlook, "reason": reason,
            "confidence": "HIGH" if score >= 2 else "MEDIUM" if score == 1 else "LOW",
        }
        for score, s, side, q, stop, outlook, reason in ideas[:4]
    ]
    return {"insight": habit_insight(trading_service.get_trade_summary(db, user.id)), "suggestions": suggestions}


# ---------- the function the route calls ----------


def get_suggestions(db: Session, user: User) -> dict:
    portfolio = trading_service.get_portfolio(db, user.id)
    held = {h["symbol"]: h["quantity"] for h in portfolio["holdings"]}

    source, note = "rules", ""
    result = None
    if config.XAI_API_KEY:
        try:
            result = ask_grok(db, user)
            source = "grok"
        except Exception as error:  # network, bad JSON, wrong model name ...
            log.warning("Grok failed: %s", error)
            note = f"Grok could not be used ({type(error).__name__}), so the rule-based advisor answered."
    else:
        note = "No Grok key is set, so the rule-based advisor answered."
    if result is None:
        result = rule_based(db, user)

    cleaned = [clean_suggestion(raw, portfolio["cash"], held) for raw in result.get("suggestions", [])]
    saved = []
    for idea in filter(None, cleaned):
        row = AiSuggestion(user_id=user.id, source=source, **idea)
        db.add(row)
        db.flush()
        saved.append({"id": row.id, **idea})
    db.commit()
    return {
        "source": source,
        "note": note,
        "insight": str(result.get("insight", ""))[:300],
        "suggestions": saved,
        "disclaimer": "For learning only. This is not financial advice.",
    }
