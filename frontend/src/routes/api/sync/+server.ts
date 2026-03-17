import { env } from '$env/dynamic/private';
import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

const productionFallbackApiBase = 'https://api.komorebi-reader.com';

export const POST: RequestHandler = async ({ fetch }) => {
	const apiBase = env.YOUTUBE_FEED_API_URL ?? productionFallbackApiBase;

	const response = await fetch(new URL('/api/sync', apiBase), {
		method: 'POST'
	});

	if (!response.ok) {
		const detail = await response.text();
		return json({ ok: false, detail }, { status: response.status });
	}

	return json({ ok: true, payload: await response.json() });
};
