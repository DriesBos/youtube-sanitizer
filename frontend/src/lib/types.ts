export type FeedDensity = 'full' | 'compact' | 'text';

export type FeedItem = {
	videoId: string;
	title: string;
	channelName: string;
	publishedAt: string;
	description?: string;
	duration?: string;
	thumbnailUrl?: string;
	isWatched?: boolean;
};
