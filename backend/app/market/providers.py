"""Where prices come from.

Two providers, both with the same two methods:
    get_quotes()          -> latest price of every stock
    get_history(symbol)   -> today's price points for a chart
"""

import random
from datetime import timedelta

from app.core.clock import utcnow
from app.market.universe import STOCKS


class DemoProvider:
    """Simulated prices (a small random walk). Used when Yahoo is not available."""

    name = "demo"

    def get_quotes(self, previous: dict) -> dict:
        """Move every price a tiny bit from its previous value."""
        quotes = {}
        for symbol, info in STOCKS.items():
            old = previous.get(symbol)
            last = old["price"] if old else info["base"]
            prev_close = old["prev_close"] if old else info["base"]
            new_price = round(last * (1 + random.uniform(-0.0008, 0.0008)), 2)
            quotes[symbol] = {"price": new_price, "prev_close": prev_close}
        return quotes

    def get_history(self, symbol: str) -> list[dict]:
        """Make 78 fake 5-minute points ending now (the same every time)."""
        rng = random.Random(symbol)
        price = STOCKS[symbol]["base"]
        now = utcnow()
        points = []
        for i in range(78):
            price = round(price * (1 + rng.uniform(-0.002, 0.002)), 2)
            moment = now - timedelta(minutes=5 * (77 - i))
            points.append({"time": moment.isoformat() + "Z", "price": price})
        return points


class YahooProvider:
    """Real NSE prices from Yahoo Finance using the yfinance library.

    Yahoo data is about 15 minutes delayed. It is not an official exchange feed.
    """

    name = "yahoo"

    def get_quotes(self) -> dict:
        import yfinance as yf  # imported here so the demo works without it

        tickers = [symbol + ".NS" for symbol in STOCKS]
        data = yf.download(
            tickers,
            period="5d",
            interval="1m",
            group_by="ticker",
            progress=False,
            threads=False,
        )
        quotes = {}
        for symbol in STOCKS:
            try:
                closes = data[symbol + ".NS"]["Close"].dropna()
                last = float(closes.iloc[-1])
                today = closes.index[-1].date()
                earlier = closes[[d.date() < today for d in closes.index]]
                prev_close = float(earlier.iloc[-1]) if len(earlier) else last
                quotes[symbol] = {"price": round(last, 2), "prev_close": round(prev_close, 2)}
            except (KeyError, IndexError):
                continue  # this stock had no data, skip it
        return quotes

    def get_history(self, symbol: str) -> list[dict]:
        import yfinance as yf

        frame = yf.Ticker(symbol + ".NS").history(period="1d", interval="5m")
        if frame.empty:
            frame = yf.Ticker(symbol + ".NS").history(period="5d", interval="5m")
        return [
            {"time": moment.isoformat(), "price": round(float(close), 2)}
            for moment, close in frame["Close"].dropna().items()
        ]
