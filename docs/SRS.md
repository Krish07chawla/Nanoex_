# Software Requirements Specification: NanoEX

## 1. Introduction

**Purpose.** This document says what NanoEX must do.

**Problem.** Students learn trading from books and old charts, not from the live market. Traders who want to teach have no simple tool to show a live chart and explain their thinking to many students at once, and students have no safe place to practise.

**Scope.** A web application with a database of users, a live stock price feed, live classes run by a trader, a virtual-money trading platform for students, an AI trade advisor, and admin control of all student accounts and virtual money.

**Out of scope.** Real money, real broker orders, video or audio streaming, mobile apps.

## 2. Users

| User | Description |
|---|---|
| Admin | Manages users and sends virtual money to students |
| Trader (teacher) | Runs live classes on the live feed |
| Student | Learns, trades with virtual money, uses the AI advisor |

## 3. Functional requirements

### Accounts
- **FR-1** A person can register as a student or a trader with name, email and password. Nobody can register as admin.
- **FR-2** Users log in with email and password and stay logged in with a token. Passwords are stored hashed.
- **FR-3** After 5 wrong passwords in 5 minutes, login is blocked for a while.
- **FR-4** Each page and API call checks the user's role (admin, trader, student).
- **FR-5** The admin can disable and enable accounts. A disabled user cannot log in or use an old token.

### Virtual money (admin)
- **FR-6** The admin sees all accounts, and for students sees cash, total value and profit/loss.
- **FR-7** The admin can send virtual money to one, several, or all students, and can take money back (never below zero).
- **FR-8** Every wallet change is saved in a ledger. Every admin action is saved in an audit log.
- **FR-9** The admin can open one student's account (holdings, orders, wallet ledger).

### Live market data
- **FR-10** The system gets prices for 10 NSE stocks from a live source and refreshes them every few seconds.
- **FR-11** Prices are pushed to every logged-in browser by WebSocket.
- **FR-12** If the live source fails, the system uses a simulated feed and clearly says so on screen.
- **FR-13** The screen always shows the data source, whether it is delayed, and whether the market is open.

### Trading (student)
- **FR-14** A student can buy and sell with market, limit and stop-loss orders.
- **FR-15** Market orders fill at once at the live price. Limit and stop-loss orders wait and fill when the live price reaches them.
- **FR-16** A student can cancel or change a waiting order.
- **FR-17** The system refuses orders the student cannot afford or does not own.
- **FR-18** Each filled order has brokerage (0.03%, at most ₹20).
- **FR-19** A student has a watchlist and price alerts that notify them in the browser.
- **FR-20** A student sees holdings with live profit/loss, order history, a CSV download of trades, a wallet ledger and a leaderboard.

### Live classes
- **FR-21** A trader creates a class with a title and up to 6 stocks. The class gets a 6-letter join code.
- **FR-22** The trader starts and ends the class.
- **FR-23** While live, the trader posts notes and buy/sell ideas that show the price at that moment. Students see them instantly without refreshing.
- **FR-24** Students join with the code, ask questions, and the trader answers. Students keep private notes.
- **FR-25** Prices are saved while a class is live. After it ends, students can replay the class with a time slider.

### AI advisor
- **FR-26** A student can ask for trade ideas. Grok works as an agent: it calls tools to read the student's history, portfolio and market indicators, then returns ideas as JSON.
- **FR-27** Every idea is checked by the system (known stock, affordable or owned quantity) before it is shown.
- **FR-28** If there is no key or Grok fails, a rule-based advisor answers instead, and the screen says which one answered.
- **FR-29** Every ideas screen says: for learning only, not financial advice.
- **FR-30** The student can send an idea to the order form, but must press Buy or Sell themselves.

## 4. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-1 Security | Passwords hashed (bcrypt); secrets only in environment variables; role check on every route |
| NFR-2 Usability | Simple white interface; the same menu style for every role; clear error messages |
| NFR-3 Reliability | A price feed failure must not stop the app (fallback to demo prices) |
| NFR-4 Maintainability | Small files, one job per file, folders by layer; code guide provided |
| NFR-5 Testability | Automated tests run without internet |
| NFR-6 Portability | Runs with SQLite on a laptop and PostgreSQL in Docker |
| NFR-7 Honesty | Delayed or simulated data is always labelled; AI output is always labelled |

## 5. Constraints and assumptions
- Yahoo Finance data (through the unofficial `yfinance` library) is about 15 minutes delayed and may be rate-limited.
- NSE trades Monday to Friday 9:15 to 15:30 IST. Outside these hours prices from Yahoo do not move.
- The Grok API needs a key and may need credits.

## 6. Acceptance criteria
1. Admin sends ₹1,00,000 to a student; the student sees it in the wallet.
2. The student buys a stock; cash goes down by value plus brokerage; the holding appears.
3. A limit buy below the live price waits and fills when the price falls to it.
4. A trader starts a class and posts a note; a student in the class sees it within a second.
5. With the Yahoo source blocked, the app still works and says "DEMO feed".
6. The AI advisor never shows an idea for an unknown stock or more shares than allowed.
