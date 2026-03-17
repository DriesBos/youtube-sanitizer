import { getAuthStatus, getBackendApiBase, getFeed } from '$lib/server/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
	return {
		apiBase: getBackendApiBase(),
		authStatus: await getAuthStatus(fetch),
		feed: await getFeed(fetch)
	};
};
