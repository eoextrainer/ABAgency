# AB Agence Portfolio SPA

## Overview
Single-page application showcasing AB Agence's 17-year career, with a full event agency offering. Frontend is vanilla HTML/CSS/JS. Backend is Flask with PostgreSQL-ready endpoints and asset scanning.

## Run Locally
1. Create and activate a virtual environment.
2. Install Flask (and psycopg2 if using PostgreSQL).
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
Assets are served from the `AB_Agence/` folder. The backend scans filenames on demand and assigns categories for gallery + timeline usage. The `/assets` endpoint returns metadata used by the SPA.

## Deployment Notes
- Configure `DATABASE_URL` for PostgreSQL.
- Host static assets behind a CDN and set a reverse proxy to the Flask app.
- Enable gzip/brotli and caching headers for `/static` and `/assets`.

## Performance Optimization Checklist
- Videos lazy-load with IntersectionObserver.
- Images use `loading="lazy"` and are served from `/assets`.
- Service worker caches core UI files.
- CSS/JS can be minified for production.
- Consider WebP/AVIF conversion for still images.
