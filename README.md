# YouTube Sanitizer

Small two-part app for a single-user YouTube subscription feed.

## Current state

- Frontend: SvelteKit in `frontend/`
- Backend: FastAPI in `backend/`
- Production backend currently live at `http://18.198.187.97`
- API endpoints currently available:
  - `GET /api/health`
  - `GET /api/feed?limit=60`
  - `POST /api/feed/{videoId}/watched`

## Repo structure

- `frontend/`: Netlify-hosted UI
- `backend/`: Lightsail-hosted API
- `netlify.toml`: Netlify build settings

## Local development

Frontend:

```sh
cd frontend
cp .env.example .env
npm install
npm run dev
```

Backend:

```sh
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --app-dir src --reload
```

## Production server

- Host: `18.198.187.97`
- Service name: `youtube-sanitizer-api`
- App location: `/srv/youtube-sanitizer`
- Reverse proxy: `caddy`

Useful commands on the server:

```sh
sudo systemctl status youtube-sanitizer-api
sudo systemctl restart youtube-sanitizer-api
sudo systemctl status caddy
sudo journalctl -u youtube-sanitizer-api -n 100 --no-pager
```

## Pending DNS / domain work

Add these DNS records for `komorebi-reader.com`:

- `A` record: `api` -> `18.198.187.97`
- `CNAME` record: `youtubefeed` -> Netlify target shown in Netlify's custom-domain UI

Once those resolve, switch the backend to:

- `https://api.komorebi-reader.com`

and set the frontend custom domain to:

- `https://youtubefeed.komorebi-reader.com`

## Current external blockers

- `api.komorebi-reader.com` now resolves to the new Lightsail server.
- Caddy has already obtained a certificate for `api.komorebi-reader.com`.
- Public HTTP on port `80` works and redirects correctly.
- Public HTTPS on port `443` still does not complete, which strongly suggests the Lightsail networking firewall still needs `HTTPS` opened.
- `youtubefeed.komorebi-reader.com` was still not resolving at the last check, so the Netlify custom-domain side was not externally reachable yet.

## Netlify settings

Build settings are already in `netlify.toml`.

Required environment variable:

```txt
YOUTUBE_FEED_API_URL=https://api.komorebi-reader.com
```

Temporary fallback if DNS is not ready yet:

```txt
YOUTUBE_FEED_API_URL=http://18.198.187.97
```

The fallback works functionally, but the custom domain should replace it as soon as DNS is in place.
