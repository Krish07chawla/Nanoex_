"""The heartbeat of the app: runs every few seconds.

Each round it (1) gets new prices, (2) fills waiting orders, (3) checks price
alerts, (4) saves prices for live classes and (5) sends everything to browsers.
"""

import asyncio
import logging

from app import config
from app.core.ws_manager import manager
from app.database import SessionLocal
from app.market.feed import feed
from app.services import alert_service, classroom_service, trading_service

log = logging.getLogger("ticks")


def handle_tick(prices: dict) -> list[dict]:
    """Do the database work for one price update. Returns messages for users."""
    with SessionLocal() as db:
        events = trading_service.process_pending_orders(db, prices)
        events += alert_service.check_alerts(db, prices)
        classroom_service.save_ticks(db, prices)
    return events


async def run_feed_loop():
    while True:
        try:
            prices = await asyncio.to_thread(feed.refresh)
            events = await asyncio.to_thread(handle_tick, prices)
            await manager.send_market(feed.snapshot())
            for event in events:
                await manager.send_user(event["user_id"], event)
        except Exception:  # keep the loop alive whatever happens
            log.exception("Feed loop error")
        await asyncio.sleep(config.FEED_SECONDS)
