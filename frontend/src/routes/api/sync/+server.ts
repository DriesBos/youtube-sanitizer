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
		const payload = await response
			.json()
			.catch(async () => ({ detail: await response.text().catch(() => 'Sync failed.') }));
		return json({ ok: false, detail: payload.detail ?? 'Sync failed.' }, { status: response.status });
	}

	return json({ ok: true, payload: await response.json() });
};
