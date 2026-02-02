# AB Agence Portfolio SPA

## Overview
Single-page application showcasing AB Agence's 17-year career, with a full event agency offering. Frontend is vanilla HTML/CSS/JS. Backend is Flask with PostgreSQL-ready endpoints and asset scanning.

## Run Locally
1. Create and activate a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Run the app:

```bash
python app.py
```

App runs at `http://127.0.0.1:5000`.

## Database
Schema: `schema.sql`
Sample data: `sample_data.sql`

Set `DATABASE_URL` to enable PostgreSQL inserts for inquiries.

## Asset Organization
Assets are served from the `assets/` folder. The backend scans filenames on demand and assigns categories for gallery + timeline usage. The `/assets` endpoint returns metadata used by the SPA.

## Email Delivery (Form -> Email)
The inquiry form can send emails via SMTP. Configure these environment variables:
- `SMTP_HOST` (required)
- `SMTP_PORT` (default: 587)
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_USE_TLS` (default: true)
- `SMTP_FROM` (default: SMTP_USERNAME)
- `SMTP_TO` (default: roum1990@hotmail.fr)

If `SMTP_HOST` is not set, inquiries are stored in `inquiries.jsonl`.

## Docker
Build and run locally with Docker Compose:
```bash
docker compose up --build
```

## Healthcheck, Rollback, Self‑Heal (Scripts)
These scripts provide basic operational safety:
- `scripts/healthcheck.sh` checks `/` and `/assets`.
- `scripts/rollback.sh` checks out a tag and restarts via Docker Compose if available.
- `scripts/self_heal.sh` runs healthcheck and triggers rollback on failure.

Set `LAST_GOOD_TAG` to a known stable tag before using rollback.

## Render Deployment (Step‑by‑Step)
1. **Create a GitHub repo** and push this project.
2. **Render Web Service**
	- Environment: Python
	- Build command: `pip install -r requirements.txt`
	- Start command: `gunicorn app:app`
3. **Add Environment Variables**
	- `DATABASE_URL` (Render Postgres connection string)
	- `PYTHON_VERSION` (e.g. 3.11.8)
	- SMTP vars (see Email Delivery section)
4. **Create Render PostgreSQL** and copy its `DATABASE_URL`.
5. **Seed the database** (from your local machine):
	```bash
	psql "$DATABASE_URL" -f schema.sql
	psql "$DATABASE_URL" -f sample_data.sql
	```
6. **Assets**
	- Keep assets in the `assets/` folder. Render will serve them via Flask.
7. **Verify**
	- `https://<your-service>.onrender.com/`
	- `https://<your-service>.onrender.com/assets`

## Deployment Notes
- Configure `DATABASE_URL` for PostgreSQL.
- Host static assets behind a CDN if needed.
- Enable gzip/brotli and caching headers for `/static` and `/assets`.

## Performance Optimization Checklist
- Videos lazy-load with IntersectionObserver.
- Images use `loading="lazy"` and are served from `/assets`.
- Service worker caches core UI files.
- CSS/JS can be minified for production.
- Consider WebP/AVIF conversion for still images.
