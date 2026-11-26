# Test plan

## 1. Strategy

| Level | What | Tool |
|---|---|---|
| Unit | Single functions: indicators, charges, price feed, advisor checks | pytest |
| API / integration | Real HTTP calls against the app with a temporary database | pytest + FastAPI TestClient |
| Build check | The website compiles | `npm run build` |
| Manual / end-to-end | A browser walk-through of all three roles (see section 5) | Headless Chrome script + manual |

**Rules for tests**
- They never use the internet. Prices are set by hand, Yahoo is replaced by a fake table, and Grok is replaced by a fake function.
- Every test starts with an empty database.

## 2. How to run

```bash
cd backend
python -m pytest -q
```

Result when this plan was written: **45 passed**.

## 3. Requirement to test table

| Requirement | Test file and test |
|---|---|
| FR-1 register, no admin signup | `test_auth.py`: register_and_login, duplicate_email, nobody_can_register_as_admin |
| FR-2 login | `test_auth.py`: wrong_password_is_rejected |
| FR-3 login blocking | `test_auth.py`: too_many_wrong_passwords_are_blocked |
| FR-4 role checks | `test_auth.py`: pages_need_login, student_cannot_use_admin_pages, trader_cannot_trade |
| FR-5 disable accounts | `test_auth.py`: disabled_user_cannot_log_in |
| FR-6, FR-9 admin sees accounts | `test_admin_wallet.py`: admin_sees_student_account_details |
| FR-7 send / take back money | `test_admin_wallet.py`: admin_sends_money, send_to_all_students, cannot_take_back_more_than_balance, student_cannot_send_money |
| FR-8 ledger and audit | `test_admin_wallet.py`: money_actions_are_in_the_audit_log |
| FR-10 to FR-13 price feed | `test_feed.py`: all five tests (demo feed, small steps, Yahoo table parsing, fallback to demo, history) |
| FR-14, FR-15 orders | `test_trading.py`: market_buy, sell_makes_profit, limit_buy_waits_then_fills, stop_loss_sells |
| FR-16 cancel / change | `test_trading.py`: cancel_and_edit_waiting_order |
| FR-17 refuse bad orders | `test_trading.py`: cannot_buy_without_enough_cash, cannot_sell_shares_you_do_not_own, stop_loss_is_only_for_selling |
| FR-18 charges | `test_trading.py`: market_buy_uses_cash_and_adds_holding (checks brokerage) |
| FR-19 watchlist, alerts | `test_trading.py`: watchlist_and_alerts |
| FR-20 portfolio, CSV, leaderboard | `test_trading.py`: portfolio_profit_uses_live_price, average_price, trade_export_is_csv, leaderboard_ranks_by_return |
| FR-21 to FR-25 classes | `test_classes.py`: full_class_flow, only_traders_can_create_classes, cannot_open_without_joining, other_trader_cannot_run_my_class, wrong_code, prices_saved_for_replay |
| FR-26 Grok agent | `test_advisor.py`: grok_agent_calls_tools_then_answers |
| FR-27 idea checks | `test_advisor.py`: bad_ideas_are_dropped (and the Grok test, which cuts 9999 shares to what cash allows) |
| FR-28 fallback | `test_advisor.py`: rule_based_advisor_works_without_a_key, falls_back_to_rules_when_grok_fails, rule_advisor_uses_the_students_own_positions |

## 4. Not covered by automatic tests (honest list)
- The real Yahoo Finance connection (tests use a fake table shaped like yfinance output). Test it by running the app on a normal internet connection and checking the top bar says "Yahoo Finance".
- The real Grok API (tests use a fake Grok). Test it with your own key.
- WebSocket delivery was checked in the browser walk-through, not in pytest.
- Docker build and Render deployment.
- Page layout on phones.

## 5. Manual walk-through (acceptance test)
1. Log in as admin. Send ₹1,00,000 to a student.
2. Log in as the student (second browser). Dashboard shows the money.
3. Market page: buy 1 share. Orders and Portfolio update.
4. Log in as a trader (third browser). Create a class, start it, post a note.
5. Student joins with the code and sees the note without refreshing.
6. Trader ends the class. Student opens the replay.
7. Student opens the AI advisor and gets ideas; "Try this idea" fills the order form.

This walk-through was run with a headless Chrome script on the demo feed and passed.
