# YouTube Sanitizer

Single-user YouTube subscription feed with:

- `frontend/`: SvelteKit UI on Netlify
- `backend/`: FastAPI API on Lightsail
- chronological cached feed data in SQLite
- in-feed YouTube playback

## Live URLs

- Frontend: `https://youtube-sanitiser.netlify.app`
- Backend: `https://api.komorebi-reader.com`

## Current status

- Frontend and backend are deployed.
- Watched-state persistence is live.
- Google OAuth and YouTube sync endpoints are implemented.
- Real YouTube data is blocked only by missing Google OAuth credentials on the backend.

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
- App location: `/srv/youtube-sanitizer`
- Service: `youtube-sanitizer-api`
- Reverse proxy: `caddy`

Useful commands on the server:

```sh
sudo systemctl status youtube-sanitizer-api
sudo systemctl restart youtube-sanitizer-api
sudo journalctl -u youtube-sanitizer-api -n 100 --no-pager
sudo systemctl status caddy
```

## Netlify

`netlify.toml` contains the build settings. Required environment variable:

```txt
YOUTUBE_FEED_API_URL=https://api.komorebi-reader.com
```

## Google OAuth setup

Create a Google Cloud OAuth web application and configure:

- Authorized JavaScript origins:
  - `https://youtube-sanitiser.netlify.app`
- Authorized redirect URIs:
  - `https://api.komorebi-reader.com/api/auth/google/callback`

Then set these in `backend/.env` on the server:

```txt
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
APP_BASE_URL=https://api.komorebi-reader.com
FRONTEND_BASE_URL=https://youtube-sanitiser.netlify.app
FRONTEND_BASE_URLS=https://youtube-sanitiser.netlify.app
```
