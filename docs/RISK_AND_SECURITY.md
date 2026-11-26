# Risks and security

## 1. Project risks

| Risk | Chance | Effect | What we did |
|---|---|---|---|
| Yahoo blocks or slows requests (unofficial source) | Medium | No real prices | Automatic fallback to a labelled demo feed; 15-second polling; history cache |
| Prices are 15 minutes delayed, so "live" is not exact | Certain | Students may think it is real-time | Top bar always says "delayed about 15 minutes" |
| AI gives a bad or made-up idea | Medium | Wrong learning | Every idea is checked by code (known stock, affordable quantity); "not financial advice" on screen; student must press Buy themselves |
| Grok key missing, no credits, or wrong model name | Medium | AI feature down | Rule-based advisor answers and the screen says why |
| Free hosting sleeps or deletes data | High | Slow first load, lost data | Documented; use PostgreSQL; use local Docker for the main demo |
| Students think virtual profit is real skill | Low | Wrong expectations | Disclaimer in the top bar of every page |

## 2. Security measures

| Area | Measure |
|---|---|
| Passwords | Hashed with bcrypt; never stored or logged as text |
| Login | Signed tokens that expire (8 hours); 5 wrong tries per 5 minutes blocks login |
| Access | Every route checks the role; a student cannot use admin or trader routes (tested) |
| Disabled accounts | Old tokens stop working at once (tested) |
| Ownership | Students can only see and change their own orders, wallet and portfolio; class pages need the join code |
| Admin signup | Not possible from the register form (tested) |
| Secrets | Only in environment variables or `.env` (which is in `.gitignore`). The Grok key is never sent to the browser |
| Input | All input is checked by Pydantic (types, lengths, ranges) |
| SQL | SQLAlchemy is used everywhere, so SQL injection is not possible from our queries |
| Audit | Admin money moves and account changes are written to an audit log |

## 3. Known limitations (honest)

- The login token is sent in the WebSocket address (`?token=`). This is common for simple apps but can appear in server logs. A production app would use a short-lived ticket instead.
- The login-attempt counter is kept in memory, so it resets when the server restarts and does not work across several servers.
- Money is stored as decimal numbers (floats) rounded to 2 places. Fine for virtual money; a real finance app would use integers (paise) or Decimal.
- Waiting buy orders do not reserve cash. Cash is checked again when the order fills, and the order is rejected if the money is gone.
- There is no email verification or password reset. A trader can register without approval (the admin can disable them).
- Holidays are not known, so "market open" may be wrong on an NSE holiday.
- Free Render databases expire after a limited time.
