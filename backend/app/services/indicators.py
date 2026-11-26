"""Simple price indicators used by the AI advisor."""


def sma(values: list[float], days: int) -> float | None:
    """Simple moving average of the last N values."""
    if len(values) < days:
        return None
    return sum(values[-days:]) / days


def rsi(values: list[float], period: int = 14) -> float | None:
    """Relative Strength Index (0 to 100). Above 70 = rising fast, below 30 = falling fast."""
    if len(values) < period + 1:
        return None
    gains = 0.0
    losses = 0.0
    for i in range(len(values) - period, len(values)):
        change = values[i] - values[i - 1]
        if change > 0:
            gains += change
        else:
            losses -= change
    if losses == 0:
        return 100.0
    strength = (gains / period) / (losses / period)
    return round(100 - 100 / (1 + strength), 1)


def describe(values: list[float]) -> dict:
    """Trend and RSI for a list of prices (oldest first)."""
    short = sma(values, 5)
    long = sma(values, 20)
    if short is None or long is None:
        trend = "UNKNOWN"
    elif short > long * 1.001:
        trend = "UP"
    elif short < long * 0.999:
        trend = "DOWN"
    else:
        trend = "SIDEWAYS"
    return {
        "trend": trend,
        "rsi": rsi(values),
        "sma5": round(short, 2) if short else None,
        "sma20": round(long, 2) if long else None,
    }
