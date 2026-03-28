# NC

Public repository for the `NATAL.KR` chart UI and its FastAPI chart-calculation backend.

## What Is Included

- Vite + React frontend for the public and internal chart views
- FastAPI backend for chart calculation and storage routes
- 64-key CSV data and symbol assets used by the wheel UI
- Swiss Ephemeris data file currently used in this workspace

## Local Run

Frontend:

```bash
npm install
npm run dev
```

Backend:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

## Deployment Notes

- Frontend expects the API at `/api/...`
- For split deployment, set `window.__ASTRO_API_BASE__`
- Default internal password is `7009`

## WordPress iframe

```html
<iframe
  src="https://your-deployment-url"
  width="100%"
  height="1600"
  style="border:0;"
  loading="lazy"
  allow="clipboard-write">
</iframe>
```

## Licensing Note

This repository is being prepared as a public source release because the current app uses freely available ephemeris-based sources and related chart-calculation assets.
