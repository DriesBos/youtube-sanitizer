import { getFeed } from '$lib/server/feed';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
	return {
		feed: await getFeed(fetch)
	};
};
