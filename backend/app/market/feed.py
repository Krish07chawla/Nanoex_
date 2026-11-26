"""The price feed: keeps the latest price of every stock in memory."""

import logging
import time
from datetime import timedelta

from app import config
from app.core.clock import utcnow
from app.market.providers import DemoProvider, YahooProvider
from app.market.universe import STOCKS

log = logging.getLogger("feed")


def is_market_open() -> bool:
    """NSE trades Monday to Friday, 9:15 to 15:30 Indian time (holidays ignored)."""
    now_ist = utcnow() + timedelta(hours=5, minutes=30)
    if now_ist.weekday() >= 5:
        return False
    minutes = now_ist.hour * 60 + now_ist.minute
    return 9 * 60 + 15 <= minutes <= 15 * 60 + 30


class PriceFeed:
    def __init__(self):
        self.latest = {}  # {"TCS": {"price": 3200.5, "prev_close": 3190.0}}
        self.source = "starting"  # "yahoo" or "demo"
        self.updated_at = None
        self._demo = DemoProvider()
        self._last_yahoo_call = 0.0
        self._history_cache = {}  # {"TCS": (time_saved, points)}

    def refresh(self) -> dict:
        """Get new prices. This blocks, so the loop runs it in a thread."""
        if config.MARKET_PROVIDER == "yahoo":
            if time.time() - self._last_yahoo_call >= config.YAHOO_SECONDS:
                self._last_yahoo_call = time.time()
                self._refresh_from_yahoo()
            elif self.source == "yahoo":
                return self.latest  # asked Yahoo recently, nothing new yet
        if self.source != "yahoo":
            self.latest = self._demo.get_quotes(self.latest)
            self.source = "demo"
            self.updated_at = utcnow()
        return self.latest

    def _refresh_from_yahoo(self):
        try:
            quotes = YahooProvider().get_quotes()
        except Exception as error:  # Yahoo can fail in many ways
            log.warning("Yahoo failed, using demo prices: %s", error)
            quotes = {}
        if quotes:
            # Any stock Yahoo did not return keeps its old (or demo) price
            missing = self._demo.get_quotes(self.latest)
            for symbol in STOCKS:
                if symbol not in quotes:
                    quotes[symbol] = missing[symbol]
            self.latest = quotes
            self.source = "yahoo"
            self.updated_at = utcnow()
        else:
            self.source = "demo"

    def price(self, symbol: str) -> float | None:
        quote = self.latest.get(symbol)
        return quote["price"] if quote else None

    def set_price(self, symbol: str, price: float, prev_close: float | None = None):
        """Set a price by hand (used by tests)."""
        self.latest[symbol] = {"price": price, "prev_close": prev_close or price}

    def snapshot(self) -> dict:
        """What we send to browsers."""
        return {
            "type": "prices",
            "source": self.source,
            "delayed": self.source == "yahoo",
            "market_open": is_market_open(),
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
            "prices": self.latest,
        }

    def _demo_history_ending_at_live_price(self, symbol: str) -> list[dict]:
        """Fake history, scaled so its last point matches the current live price."""
        points = self._demo.get_history(symbol)
        live = self.price(symbol)
        if live:
            scale = live / points[-1]["price"]
            points = [{"time": p["time"], "price": round(p["price"] * scale, 2)} for p in points]
        return points

    def get_history(self, symbol: str) -> list[dict]:
        """Chart points for one stock. Saved for 60 seconds to be gentle on Yahoo."""
        saved = self._history_cache.get(symbol)
        if saved and time.time() - saved[0] < 60:
            return saved[1]
        points = []
        if self.source == "yahoo":
            try:
                points = YahooProvider().get_history(symbol)
            except Exception as error:
                log.warning("History failed for %s: %s", symbol, error)
        if not points:
            points = self._demo_history_ending_at_live_price(symbol)
        self._history_cache[symbol] = (time.time(), points)
        return points


# One shared feed for the whole app
feed = PriceFeed()
