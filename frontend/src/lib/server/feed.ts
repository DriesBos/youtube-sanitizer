import { dev } from '$app/environment';
import { env } from '$env/dynamic/private';
import type { FeedItem } from '$lib/types';

const productionFallbackApiBase = 'http://18.198.187.97';

const seedFeed: FeedItem[] = [
	{
		videoId: 'dQw4w9WgXcQ',
		title: 'A surprisingly sharp breakdown of modern web performance',
		channelName: 'Frontend Field Notes',
		publishedAt: '2026-03-17T13:10:00Z',
		duration: '18:24',
		description: 'A seed item that stands in for the eventual backend feed.',
		isWatched: false
	},
	{
		videoId: '3JZ_D3ELwOQ',
		title: 'Weekly design systems review and release notes',
		channelName: 'Component Office',
		publishedAt: '2026-03-17T11:40:00Z',
		duration: '26:41',
		description: 'Seed content keeps the page usable while the backend is still being built.',
		isWatched: true
	},
	{
		videoId: 'L_jWHffIx5E',
		title: 'Shipping a tiny app with fewer moving parts',
		channelName: 'Quiet Architecture',
		publishedAt: '2026-03-16T19:05:00Z',
		duration: '12:09',
		description: 'Chronological ordering is applied server-side before the page renders.',
		isWatched: false
	},
	{
		videoId: 'Zi_XLOBDo_Y',
		title: 'The case for server-owned feeds and cached merges',
		channelName: 'Systems Weekly',
		publishedAt: '2026-03-16T16:25:00Z',
		duration: '31:12',
		description: 'The UI accepts optional watched status from the backend when it exists.',
		isWatched: false
	},
	{
		videoId: 'fJ9rUzIMcZQ',
		title: 'What actually matters for a single-user media app',
		channelName: 'One Box Ops',
		publishedAt: '2026-03-15T22:15:00Z',
		duration: '9:58',
		description: 'Local watched-state can bridge the gap until a richer backend exists.',
		isWatched: true
	}
];

type FeedApiResponse =
	| FeedItem[]
	| {
			items?: FeedItem[];
			feed?: FeedItem[];
	  };

function sortChronologically(items: FeedItem[]): FeedItem[] {
	return [...items].sort((left, right) => {
		return new Date(right.publishedAt).getTime() - new Date(left.publishedAt).getTime();
	});
}

function normaliseFeed(items: FeedItem[]): FeedItem[] {
	return sortChronologically(
		items.map((item) => ({
			...item,
			isWatched: item.isWatched ?? false
		}))
	);
}

export async function getFeed(fetchFn: typeof fetch): Promise<FeedItem[]> {
	const apiBase = env.YOUTUBE_FEED_API_URL ?? (dev ? undefined : productionFallbackApiBase);

	if (!apiBase) {
		return normaliseFeed(seedFeed);
	}

	try {
		const response = await fetchFn(new URL('/api/feed?limit=60', apiBase));

		if (!response.ok) {
			throw new Error(`Feed request failed with ${response.status}`);
		}

		const payload = (await response.json()) as FeedApiResponse;
		const items = Array.isArray(payload) ? payload : payload.items ?? payload.feed ?? [];

		if (items.length === 0) {
			return normaliseFeed(seedFeed);
		}

		return normaliseFeed(items);
	} catch (error) {
		console.error('Falling back to seeded feed data.', error);
		return normaliseFeed(seedFeed);
	}
}
