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
- `GET /api/feed?limit=60`

## Deployment shape

- FastAPI + Uvicorn
- SQLite on local disk
- systemd service
- Caddy reverse proxy
