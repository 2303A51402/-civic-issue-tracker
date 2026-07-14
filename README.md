# Civic Issue Tracker — Backend API

FastAPI backend for a civic issue reporting platform. Citizens report local issues
(potholes, garbage, streetlights, water leakage) with photo + location, track status,
and admins manage resolution — with every status change logged for analytics.

## Tested and working
Signup, login, authenticated report creation, public report listing, and status
history logging have all been verified end-to-end.

## Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000/docs` for interactive Swagger UI — try every endpoint
without writing frontend code first.

Uses SQLite by default (`civic_tracker.db`, auto-created) — zero setup needed to start.

## API overview

**Auth**
- `POST /auth/signup` — create citizen account, returns JWT
- `POST /auth/login` — returns JWT

**Reports**
- `POST /reports` — create a report (auth required)
- `GET /reports` — public list, filterable by `category` and `status`
- `GET /reports/mine` — current user's reports (auth required)
- `GET /reports/{id}` — single report with full status history
- `PATCH /reports/{id}/status` — update status (admin only) — logs to StatusHistory
- `POST /reports/upload-photo` — upload a report photo (auth required)
- `GET /reports/analytics/summary` — counts by category/status (admin only)

## Making a user an admin

There's no signup flow for admins by design (citizens shouldn't self-promote).
After creating a user via `/auth/signup`, promote them manually:

```python
# quick_promote.py
from app.database import SessionLocal
from app import models

db = SessionLocal()
user = db.query(models.User).filter(models.User.email == "you@example.com").first()
user.role = models.UserRole.admin
db.commit()
```

## Deploying to Render (matches your other projects' setup)

1. Push this folder to a GitHub repo
2. On Render: New → Web Service → connect the repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   - `SECRET_KEY` — any long random string
   - `DATABASE_URL` — Render's free Postgres connection string (switches you off SQLite automatically — no code changes needed)
6. Once live, your Swagger docs are at `https://your-app.onrender.com/docs`

## What's next (frontend milestones)

- React + Tailwind report submission form (photo upload, category picker)
- Leaflet.js map plotting all reports, color-coded by status
- "Track my report" lookup page
- Admin panel to update statuses
- Export data → Power BI/Tableau for the analytics dashboard (the differentiator
  for your portfolio — reuses your Retail Analytics Dashboard skills)

## Schema note

The `StatusHistory` table logs every status transition with a timestamp. This is
what lets you later compute accurate "average resolution time" and "status change
trend" charts in Power BI/Tableau — it's easy to skip this table early on, but hard
to backfill later, so it's built in from the start.
