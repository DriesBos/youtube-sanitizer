# Frontend

SvelteKit frontend for the YouTube subscription feed.

## Local run

From the repo root:

```sh
cd frontend
cp .env.example .env
npm install
npm run dev
```

The frontend will start on `http://localhost:5173`.

If you have a backend running locally, point `YOUTUBE_FEED_API_URL` at it in `frontend/.env`.
If you do not, the app falls back to seeded demo feed data.

## Build

```sh
cd frontend
npm run check
npm run build
```

## Netlify

The repo root includes a `netlify.toml` that sets:

- base directory: `frontend`
- build command: `npm run build`
- Node version: `22.22.0`

For frontend env vars in Netlify, add:

```txt
YOUTUBE_FEED_API_URL=https://your-backend-domain
```

This variable is read server-side by SvelteKit when building/rendering the frontend.
