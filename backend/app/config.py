"""App settings. Values come from environment variables (or a .env file)."""

import os

from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nanoex.db")

# Login tokens
JWT_SECRET = os.getenv("JWT_SECRET", "development-only-secret-change-it-in-production")
JWT_HOURS = int(os.getenv("JWT_HOURS", "8"))

# First admin account
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@nanoex.in")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "ChangeMe123")

# Price feed
MARKET_PROVIDER = os.getenv("MARKET_PROVIDER", "yahoo")  # "yahoo" or "demo"
START_FEED = os.getenv("START_FEED", "true").lower() == "true"
FEED_SECONDS = float(os.getenv("FEED_SECONDS", "5"))  # how often we broadcast
YAHOO_SECONDS = float(os.getenv("YAHOO_SECONDS", "15"))  # how often we ask Yahoo

# AI advisor (Grok from xAI)
XAI_API_KEY = os.getenv("XAI_API_KEY", "")
XAI_MODEL = os.getenv("XAI_MODEL", "grok-4")
XAI_BASE_URL = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")

# Trading rules
BROKERAGE_RATE = 0.0003  # 0.03% of trade value ...
BROKERAGE_MAX = 20.0  # ... but never more than Rs 20 per order
