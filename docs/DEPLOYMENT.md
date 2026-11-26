# Deployment

The app is one container: the Python server also serves the built website. It needs one database and three secrets.

## Environment variables

| Name | Meaning |
|---|---|
| `DATABASE_URL` | Database address (PostgreSQL in production) |
| `JWT_SECRET` | Long random text that signs login tokens |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | The first admin account |
| `MARKET_PROVIDER` | `yahoo` or `demo` |
| `XAI_API_KEY`, `XAI_MODEL` | Grok key and model (optional) |

Never put these in Git. Make a secret with:
`python -c "import secrets; print(secrets.token_urlsafe(48))"`

## Option A: Docker on your computer (best for the demo)

Create a file named `.env` next to `docker-compose.yml`:

```
JWT_SECRET=paste-a-long-random-text
ADMIN_PASSWORD=choose-a-strong-password
XAI_API_KEY=
```

Then:

```bash
docker compose up --build
```

Open http://localhost:8000. The first start takes a few minutes.

## Option B: Render (public link)

1. Put the project on GitHub (the `.env` file is ignored by `.gitignore`).
2. On render.com choose **New > Blueprint** and select the repository. Render reads `render.yaml`.
3. When asked, type `ADMIN_PASSWORD` and (optionally) `XAI_API_KEY`.
4. Wait for the build. Open the link Render gives you. Check `/api/health` shows `{"status":"ok"}`.

**Things to know**
- A free web service goes to sleep when nobody uses it, so the first visit can take about a minute.
- Free databases on Render are time-limited. Check the plan in the Render page before relying on the data.
- Yahoo may block requests from cloud servers. If the top bar says "DEMO feed", Yahoo was not reachable from the server and prices are simulated.
- Make sure you can answer in your report: which feed was used during the demo.

## Check list before the demo
- [ ] `/api/health` works
- [ ] Admin can log in
- [ ] Top bar shows the expected price source
- [ ] A student has received virtual money
- [ ] A class can be created, started and seen by a student in a second browser
