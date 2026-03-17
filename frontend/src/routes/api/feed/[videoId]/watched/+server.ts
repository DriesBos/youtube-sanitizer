import { dev } from '$app/environment';
import { env } from '$env/dynamic/private';
import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

const productionFallbackApiBase = 'http://18.198.187.97';

export const POST: RequestHandler = async ({ params, fetch }) => {
	const apiBase = env.YOUTUBE_FEED_API_URL ?? (dev ? undefined : productionFallbackApiBase);

	if (!apiBase) {
		return json({ ok: true, persisted: false, fallback: true });
	}

	const response = await fetch(new URL(`/api/feed/${params.videoId}/watched`, apiBase), {
		method: 'POST'
	});

	if (!response.ok) {
		return json(
			{
				ok: false,
				error: 'Failed to persist watched state'
			},
			{ status: response.status }
		);
	}

	const payload = await response.json();
	return json({ ok: true, persisted: true, payload });
};
