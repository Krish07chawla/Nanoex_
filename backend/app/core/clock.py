"""One place for "what time is it now". Times are stored in UTC."""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Current UTC time without timezone info (simple for SQLite)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
