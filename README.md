# TravelBud

Personalized travel itinerary planner: pick a route, dates, and budget; choose from the top attractions at your destination; get the cheapest flight + hotel bundle for your dates and an AI-generated day-by-day itinerary (English, Spanish, or Hindi) as a downloadable PDF.

> This is a full rebuild of the original 2023 Streamlit + FastAPI project (preserved in [`legacy/`](legacy/)) as a modern webapp: **Next.js frontend + modernized FastAPI backend + Claude API**.

## Architecture

```
Browser ── Next.js (App Router, TypeScript, Tailwind, recharts)
              │  typed API client; JWT in httpOnly cookies
              │  (Next rewrites proxy /api/* → FastAPI, same-origin cookies)
              ▼
          FastAPI (routers → services → providers)
              ├─ auth: bcrypt + JWT access/refresh cookies, role-based admin
              ├─ attractions: Google Places + greedy distance pairing (24h TTL cache,
              │               static fallback when no key)
              ├─ pricing: provider interface — Mock (default) or Amadeus test tier
              ├─ itinerary: Anthropic Claude — generation AND translation
              ├─ pdf: fpdf2 in-memory (bundled Noto fonts for Spanish/Hindi)
              │       storage: local dir (default) or S3
              └─ SQLAlchemy 2.x + Alembic ── PostgreSQL
```

## Quickstart

```bash
cp .env.example .env       # set at least ANTHROPIC_API_KEY and JWT_SECRET
docker compose up --build
```

- Web: http://localhost:3000
- API docs: http://localhost:8000/docs
- Admin login: `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` from your `.env`

Migrations and seeding (plans + admin user) run automatically on API startup.

### Local dev without Docker

```bash
# backend
cd backend
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
docker compose up -d db            # or point DATABASE_URL at your own Postgres
.venv/bin/alembic upgrade head && .venv/bin/python -m app.db.seed
.venv/bin/uvicorn app.main:app --reload

# frontend (second terminal)
cd frontend
npm install && npm run dev
```

### Tests

```bash
cd backend && .venv/bin/pytest     # 14 tests: auth, RBAC, pricing, rate limits, PDF
cd frontend && npm run lint && npx tsc --noEmit
```

## Configuration matrix

The app degrades gracefully — it runs end-to-end with only an Anthropic key:

| Key | Without it | With it |
|---|---|---|
| `ANTHROPIC_API_KEY` | template-based offline itinerary, no translation | Claude generates + translates itineraries |
| `GOOGLE_MAPS_API_KEY` | static sample attractions, pseudo-distances | real Places top-10 + Distance Matrix pairing |
| `AMADEUS_CLIENT_ID/SECRET` + `PRICING_PROVIDER=amadeus` | deterministic mock hotels/flights | real Amadeus test-tier prices |
| `STORAGE_BACKEND=s3` + AWS creds | PDFs cached in a local dir | PDFs stored in S3 |

## Features

- Multi-step trip wizard: city/IATA autocomplete (7k airports bundled), dates, party size, flight preference (Best/Cheapest/Fastest/Direct), budget slider
- Cheapest flight+hotel bundle across every valid date window in your range, with over-budget warning
- Attractions paired by proximity so each day's stops are close together
- Itineraries persisted and re-downloadable as PDFs; Unicode fonts so Hindi/Spanish render correctly
- Plan tiers (Basic 10 / Standard 25 / Premium 50 requests) with rate limiting
- Admin dashboard: users by plan, trips per day, top destinations, budget stats (aggregates only)

## Security notes

- Tokens are httpOnly cookies — never written to disk or readable by JS (the legacy app wrote them to `.env`).
- Admin endpoints require the `admin` role server-side; analytics return aggregates, never user rows.
- ⚠️ The legacy code once contained hardcoded RDS credentials which remain in git history — **those database credentials must be rotated** if that RDS instance still exists.
- Password reset is demo-grade (no email verification), matching the original app's behavior.

## Repo layout

```
frontend/   Next.js app (src/app routes, src/lib/api typed client)
backend/    FastAPI app (app/routers, app/services, app/providers, alembic, tests)
legacy/     original Streamlit + monolithic FastAPI implementation (reference only)
```
