# NanoEX

A web platform where an experienced **trader teaches students on the same day's live NSE stock prices**.
Students practise with **virtual money** sent by an **admin**, on a full trading screen, and get trade ideas from an **AI advisor (Grok)**.

> Virtual money only. Nothing here places real orders or gives financial advice.
> Prices come from Yahoo Finance (NSE) and are **about 15 minutes delayed**. If Yahoo is unreachable the app switches to a clearly labelled **simulated demo feed**.

## What each role can do

| Role | Main things |
|---|---|
| **Admin** | See every account, send or take back virtual money (one student, some, or all), disable accounts, read the audit log |
| **Trader** | Create a class, start it, post notes and buy/sell ideas on live prices, answer student questions, end the class |
| **Student** | Watch live prices and charts, buy and sell (market, limit, stop-loss), watchlist, price alerts, portfolio and profit/loss, trade history (CSV), wallet, leaderboard, join classes, replay old classes, ask the AI advisor |

## Run it on your computer

You need Python 3.12+ and Node 20+.

```bash
# 1. Backend (terminal 1)
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env               # then edit JWT_SECRET and ADMIN_PASSWORD
python -m app.seed_demo            # optional: demo trader + 2 students (password Demo1234)
uvicorn app.main:app --reload --port 8000

# 2. Website (terminal 2)
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](https://nanoex.onrender.com) and log in as the admin from your `.env`
(default `admin@nanoex.in`; set your own password in `.env`).

No database server is needed: SQLite is used by default.

## The AI advisor (Grok)

1. Get a key from https://console.x.ai (check your Billing page for free credits).
2. Put it in `backend/.env`: `XAI_API_KEY=your-key` (never in the code, never in Git).
3. If the model name in `.env` (`XAI_MODEL`) is not available to your account, change it to one listed in the xAI console.

Without a key, a simple rule-based advisor answers instead, and the screen says which one was used.

## Tests

```bash
cd backend
python -m pytest -q        # 45 tests, no internet needed
cd ../frontend
npm run build              # checks the website compiles
```

## Documents (software engineering)

| File | What it is |
|---|---|
| [docs/SRS.md](docs/SRS.md) | Requirements |
| [docs/DESIGN.md](docs/DESIGN.md) | Architecture and UML diagrams |
| [docs/AGILE_PLAN.md](docs/AGILE_PLAN.md) | Sprints and user stories |
| [docs/TEST_PLAN.md](docs/TEST_PLAN.md) | Test strategy and requirement-to-test table |
| [docs/RISK_AND_SECURITY.md](docs/RISK_AND_SECURITY.md) | Risks, security, known limits |
| [docs/USER_MANUAL.md](docs/USER_MANUAL.md) | How to use it, per role |
| [docs/CODE_GUIDE.md](docs/CODE_GUIDE.md) | Where everything is in the code |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Docker and Render |
