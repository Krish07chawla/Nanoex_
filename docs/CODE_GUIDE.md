# Code guide: where everything is

**Rules the code follows**
- One file = one job, usually under 150 lines.
- Plain functions with clear names. No clever tricks.
- A short comment at the top of every file says what it is for.
- Routes are thin. The real rules live in `services/`.

## Folder map

```
nanoex/
├── backend/                     Python (FastAPI)
│   ├── app/
│   │   ├── main.py              Starts the app, creates tables and the first admin
│   │   ├── config.py            Settings from .env
│   │   ├── database.py          Database connection
│   │   ├── seed_demo.py         Optional demo users
│   │   ├── core/
│   │   │   ├── security.py      Passwords, tokens, role checks
│   │   │   ├── constants.py     Names like BUY, SELL, STUDENT
│   │   │   ├── ws_manager.py    WebSocket connections
│   │   │   └── clock.py         Current time (UTC)
│   │   ├── models/              Database tables
│   │   │   ├── user.py          User, Wallet, WalletTransaction, AuditLog
│   │   │   ├── trading.py       Order, Holding, Watchlist, PriceAlert, AiSuggestion
│   │   │   └── classroom.py     ClassSession, notes, questions, price ticks
│   │   ├── schemas/             Shapes of incoming data (validation)
│   │   ├── routes/              Web endpoints (one file per area)
│   │   │   ├── auth.py          register, login, me
│   │   │   ├── market.py        quotes, history, watchlist, alerts
│   │   │   ├── trading.py       orders, portfolio, wallet, CSV, leaderboard
│   │   │   ├── advisor.py       AI ideas
│   │   │   ├── classes.py       live classes
│   │   │   ├── admin.py         admin tools
│   │   │   └── ws.py            WebSocket endpoint
│   │   ├── services/            The real logic
│   │   │   ├── wallet_service.py     the only place balances change
│   │   │   ├── trading_service.py    place / fill / cancel orders, portfolio
│   │   │   ├── classroom_service.py  classes, notes, questions, replay
│   │   │   ├── advisor_service.py    Grok agent + rule-based backup
│   │   │   ├── indicators.py         moving average, RSI, trend
│   │   │   ├── admin_service.py      send money, leaderboard
│   │   │   ├── alert_service.py      price alerts
│   │   │   ├── audit_service.py      audit log
│   │   │   └── tick_service.py       the 5-second loop
│   │   └── market/
│   │       ├── universe.py      The 10 stocks
│   │       ├── providers.py     Yahoo provider + demo provider
│   │       └── feed.py          Latest prices in memory
│   └── tests/                   pytest tests
├── frontend/src/                React website
│   ├── main.jsx, App.jsx        Start and page list
│   ├── api.js                   One function for all backend calls
│   ├── auth.jsx                 Logged-in user
│   ├── live.jsx                 Live prices (WebSocket)
│   ├── format.js                Money / time helpers
│   ├── components/              Navbar, PriceChart, OrderTicket
│   └── pages/                   One file per screen (+ admin/)
├── docs/                        Software engineering documents
├── Dockerfile, docker-compose.yml, render.yaml
└── .github/workflows/ci.yml     Automatic tests
```

## How one request flows (buying a stock)

1. `OrderTicket.jsx` sends `POST /api/orders` using `api.js`.
2. `routes/trading.py` checks the user is a STUDENT and the data is valid (`schemas/trading.py`).
3. `services/trading_service.place_order` checks the stock, price, and what the student owns.
4. For a market order it calls `fill_order`, which calls `wallet_service.change_balance` (money) and updates the `Holding`.
5. The route returns the order, and the screen shows "Done".

## How live prices flow

1. `tick_service.run_feed_loop` runs every 5 seconds.
2. `market/feed.py` gets prices (Yahoo, or demo if Yahoo fails).
3. Waiting orders and alerts are checked (`trading_service.process_pending_orders`, `alert_service.check_alerts`).
4. Prices of live classes are saved (`classroom_service.save_ticks`).
5. `ws_manager` sends the prices to every browser. `live.jsx` receives them and the screens update.

## Where to change things
| I want to... | Change this |
|---|---|
| Add a stock | `market/universe.py` |
| Change brokerage | `config.py` (BROKERAGE_RATE, BROKERAGE_MAX) |
| Change how often prices update | `FEED_SECONDS`, `YAHOO_SECONDS` in `.env` |
| Change the AI instructions | `SYSTEM_PROMPT` in `services/advisor_service.py` |
| Add a tool the AI can use | `TOOLS` list and `run_tool` in `advisor_service.py` |
| Change colours | `frontend/src/styles.css` (top of the file) |
