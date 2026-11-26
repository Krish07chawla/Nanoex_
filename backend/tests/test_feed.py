from app.market.feed import PriceFeed
from app.market.universe import STOCKS


def test_demo_feed_gives_a_price_for_every_stock():
    feed = PriceFeed()  # MARKET_PROVIDER is "demo" in tests
    prices = feed.refresh()
    assert set(prices) == set(STOCKS)
    assert feed.source == "demo"
    assert feed.snapshot()["delayed"] is False


def test_prices_move_only_a_little_each_step():
    feed = PriceFeed()
    first = feed.refresh()["TCS"]["price"]
    second = feed.refresh()["TCS"]["price"]
    assert abs(second - first) / first < 0.01


def test_yahoo_provider_reads_yfinance_table(monkeypatch):
    """Check our parsing with a table shaped like yfinance's real output."""
    import pandas as pd
    import yfinance

    from app.market.providers import YahooProvider

    times = pd.to_datetime(
        ["2026-11-25 15:29", "2026-11-26 09:15", "2026-11-26 09:16"]
    ).tz_localize("Asia/Kolkata")
    columns = pd.MultiIndex.from_product([["TCS.NS"], ["Close"]])
    table = pd.DataFrame([[3190.0], [3200.0], [3210.5]], index=times, columns=columns)
    monkeypatch.setattr(yfinance, "download", lambda *args, **kwargs: table)

    quotes = YahooProvider().get_quotes()
    assert quotes["TCS"] == {"price": 3210.5, "prev_close": 3190.0}
    assert "INFY" not in quotes  # no data for it, so it is skipped


def test_feed_uses_demo_prices_when_yahoo_fails(monkeypatch):
    from app import config
    from app.market import feed as feed_module

    monkeypatch.setattr(config, "MARKET_PROVIDER", "yahoo")
    monkeypatch.setattr(feed_module.YahooProvider, "get_quotes", lambda self: (_ for _ in ()).throw(RuntimeError("blocked")))
    feed = PriceFeed()
    prices = feed.refresh()
    assert feed.source == "demo" and set(prices) == set(STOCKS)


def test_history_has_points_for_a_chart():
    points = PriceFeed().get_history("TCS")
    assert len(points) == 78 and "time" in points[0] and "price" in points[0]
