"""Starts the app: creates tables, the first admin, the price loop and the routes."""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import config
from app.core import constants as c
from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models import User
from app.routes import admin, advisor, auth, classes, market, trading, ws
from app.services import wallet_service
from app.services.tick_service import run_feed_loop

logging.basicConfig(level=logging.INFO)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"  # the built website


def create_first_admin():
    """Make the admin account from .env if it does not exist yet."""
    with SessionLocal() as db:
        if not db.query(User).filter_by(email=config.ADMIN_EMAIL.lower()).first():
            admin_user = User(
                name="Admin",
                email=config.ADMIN_EMAIL.lower(),
                password_hash=hash_password(config.ADMIN_PASSWORD),
                role=c.ADMIN,
            )
            db.add(admin_user)
            db.flush()
            wallet_service.get_wallet(db, admin_user.id)
            db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    create_first_admin()
    task = asyncio.create_task(run_feed_loop()) if config.START_FEED else None
    yield
    if task:
        task.cancel()


app = FastAPI(title="NanoEX", lifespan=lifespan)

for module in (auth, market, trading, advisor, classes, admin):
    app.include_router(module.router, prefix="/api")
app.include_router(ws.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# If the website was built (static folder exists), serve it from this same app.
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def website(path: str):
        file = STATIC_DIR / path
        if path and file.is_file():
            return FileResponse(file)
        return FileResponse(STATIC_DIR / "index.html")
