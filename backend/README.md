# Backend

Lean FastAPI backend for the YouTube subscription feed.

## Local run

```sh
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --app-dir src --reload
```

The API will start on `http://127.0.0.1:8000`.

## Available endpoints

- `GET /api/health`
- `GET /api/auth/status`
- `GET /api/auth/google/start`
- `GET /api/auth/google/callback`
- `GET /api/feed?limit=60`
- `POST /api/feed/{videoId}/watched`
- `POST /api/sync`

## Google OAuth setup

Create a Google Cloud OAuth web application and set:

- Authorized JavaScript origins:
  - `https://youtube-sanitiser.netlify.app`
- Authorized redirect URIs:
  - `https://api.komorebi-reader.com/api/auth/google/callback`

Then place the credentials in `backend/.env`:

```txt
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

## Deployment shape

- FastAPI + Uvicorn
- SQLite on local disk
- systemd service
- Caddy reverse proxy
