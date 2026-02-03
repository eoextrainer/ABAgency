# Render Deployment Guide (Backend + Frontend + Database)

This guide covers:
- Exporting the local database
- Creating a Render PostgreSQL database
- Importing schema + seed data automatically from VS Code
- Deploying the Flask backend
- Serving the frontend

## 1) Prerequisites
- Render account
- GitHub repo connected to Render
- Local project ready in VS Code
- `psql` installed locally

## 2) Create the Render PostgreSQL Database
1. In Render Dashboard, create a new PostgreSQL instance.
2. Copy the **External Database URL** (not the internal one).
3. Save it as `DATABASE_URL` in your Render Web Service environment variables.

## 3) Export Local Database (SQLite)
If you used SQLite locally (`app.db`), export the schema and data:

- Schema: already in [schema.sql](schema.sql)
- Seed data: already in [sample_data.sql](sample_data.sql)

If you need to refresh the seed:
- Run `init_db()` locally to ensure all tables + seed data exist.

## 4) Import Schema + Seed to Render Postgres (from VS Code)
From the VS Code terminal, run the commands below **once** after creating the Render Postgres instance.

### 4.1) Set the connection string in VS Code
- In Render, copy the External Database URL.
- In your VS Code terminal, export it:
  - `DATABASE_URL="<Render External Database URL>"`

### 4.2) Import schema + seed
- Import schema:
  - `psql "$DATABASE_URL" -f schema.sql`
- Import seed data:
  - `psql "$DATABASE_URL" -f sample_data.sql`

If you want the multi-user demo accounts, keep sample_data.sql as-is.

## 5) Create the Render Web Service (Backend)
1. In Render, create a new **Web Service** connected to this repo.
2. Environment: **Python**
3. Build Command:
   - `pip install -r requirements.txt`
4. Start Command:
   - `gunicorn app:app`

### Required Environment Variables
- `DATABASE_URL` (from Render Postgres)
- `PYTHON_VERSION` (e.g. 3.12.1)
- SMTP vars (if email sending is required):
  - `SMTP_HOST`
  - `SMTP_PORT`
  - `SMTP_USERNAME`
  - `SMTP_PASSWORD`
  - `SMTP_USE_TLS`
  - `SMTP_FROM`
  - `SMTP_TO`

## 6) Frontend Deployment
The frontend is served by Flask from:
- [templates/index.html](templates/index.html)
- [static/](static/)

No separate frontend hosting is required unless you want a dedicated static host.

## 7) Verify Deployment
- Home: `https://<render-service>.onrender.com/`
- Assets: `https://<render-service>.onrender.com/assets`
- Workspace: `https://<render-service>.onrender.com/workspace`

## 8) Optional: Automated DB Load From VS Code
If you want a quick one-liner from VS Code:
- `psql "$DATABASE_URL" -f schema.sql && psql "$DATABASE_URL" -f sample_data.sql`

## 9) Notes
- If Render Postgres already has tables, re-running schema may fail. Drop first if needed.
- Seed data includes demo users:
  - admin@abagency.com / Admin123!
  - moderator@abagency.com / Mod123!
  - artist@abagency.com / User123!
