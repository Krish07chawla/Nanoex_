# Agile plan

**Method:** Scrum-style, one-week sprints, a working demo at the end of each sprint.

## Product backlog (user stories)

| ID | Story | Priority |
|---|---|---|
| US-1 | As a user I can register and log in so that my data is saved | High |
| US-2 | As an admin I can send virtual money to students so they can practise | High |
| US-3 | As a student I can see live prices and a chart | High |
| US-4 | As a student I can buy and sell with virtual money | High |
| US-5 | As a trader I can run a live class with notes on live prices | High |
| US-6 | As a student I can join a class, ask questions and replay it later | High |
| US-7 | As a student I can get AI trade ideas based on my history | Medium |
| US-8 | As a student I can use limit and stop-loss orders, watchlist and alerts | Medium |
| US-9 | As an admin I can see all accounts, disable users and read an audit log | Medium |
| US-10 | As a student I can see a leaderboard and download my trades | Low |

## Sprints

| Sprint | Goal | Stories | Done when |
|---|---|---|---|
| 1 | Foundation | US-1 | Register, login, roles, database, tests for login |
| 2 | Money and admin | US-2, US-9 | Admin sends money; ledger and audit log work |
| 3 | Live market | US-3 | Prices flow by WebSocket; Yahoo with demo fallback |
| 4 | Trading | US-4, US-8, US-10 | Market, limit, stop-loss orders; portfolio; CSV; leaderboard |
| 5 | Classroom | US-5, US-6 | Live notes, Q&A, saved prices, replay |
| 6 | AI and release | US-7 | Grok agent with fallback; Docker; documents; final test |

## Definition of done
- The feature works in the browser.
- It has automated tests that pass.
- Its role checks are tested (who may and may not use it).
- The code follows the code guide (small files, clear names, comments).
- The documents are updated.

## Retrospective notes (what we learned)
- Yahoo data may be blocked on some networks, so a clearly labelled fallback feed was added early.
- AI output cannot be trusted blindly, so every idea is checked by code before it is shown.
- Keeping each file small made testing much easier.
