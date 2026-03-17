<script lang="ts">
	import { onMount } from 'svelte';
	import YouTubePlayer from '$lib/components/YouTubePlayer.svelte';
	import type { FeedDensity, FeedItem } from '$lib/types';

	let { data } = $props<{ data: { feed: FeedItem[] } }>();

	const densityCycle: FeedDensity[] = ['full', 'compact', 'text'];
	const densityLabels: Record<FeedDensity, string> = {
		full: 'Full',
		compact: 'Compact',
		text: 'Text only'
	};
	const feed = $derived(data.feed);
	const serverWatchedIds = $derived(
		feed.filter((item: FeedItem) => item.isWatched).map((item: FeedItem) => item.videoId)
	);

	let density = $state<FeedDensity>('full');
	let watchedIds = $state<string[]>([]);
	let activeVideoId = $state<string | null>(null);

	const currentDensityLabel = $derived(densityLabels[density]);

	onMount(() => {
		const storedDensity = window.localStorage.getItem('feed-density');
		const storedWatched = window.localStorage.getItem('watched-video-ids');

		if (storedDensity === 'full' || storedDensity === 'compact' || storedDensity === 'text') {
			density = storedDensity;
		}

		if (storedWatched) {
			const parsed = JSON.parse(storedWatched) as string[];
			watchedIds = [...new Set(parsed)];
		}
	});

	function cycleDensity() {
		const currentIndex = densityCycle.indexOf(density);
		const nextDensity = densityCycle[(currentIndex + 1) % densityCycle.length];

		density = nextDensity;
		activeVideoId = null;
		window.localStorage.setItem('feed-density', nextDensity);
	}

	function toggleVideo(videoId: string) {
		activeVideoId = activeVideoId === videoId ? null : videoId;
	}

	function markWatched(videoId: string) {
		if (watchedIds.includes(videoId)) {
			return;
		}

		watchedIds = [...watchedIds, videoId];
		window.localStorage.setItem('watched-video-ids', JSON.stringify(watchedIds));
	}

	function isWatched(videoId: string) {
		return serverWatchedIds.includes(videoId) || watchedIds.includes(videoId);
	}

	function formatDate(date: string) {
		const value = new Date(date);
		const day = `${value.getUTCDate()}`.padStart(2, '0');
		const month = `${value.getUTCMonth() + 1}`.padStart(2, '0');
		const year = value.getUTCFullYear();

		return `${day}.${month}.${year}`;
	}

	function getThumbnailUrl(item: FeedItem) {
		return item.thumbnailUrl ?? `https://i.ytimg.com/vi/${item.videoId}/hqdefault.jpg`;
	}
</script>

<svelte:head>
	<title>Subscription Feed</title>
	<meta
		name="description"
		content="A chronological YouTube subscription feed with full, compact, and text-only views."
	/>
</svelte:head>

<div class="shell">
	<header class="topbar">
		<div>
			<p class="overline">YouTube subscription feed</p>
			<p class="caption">Chronological, cached, and built for in-feed playback.</p>
		</div>

		<button class="density-toggle" type="button" onclick={cycleDensity}>
			<img alt="" aria-hidden="true" src="/icon-btn.svg" />
			<span class="sr-only">Cycle viewing mode. Current mode: {currentDensityLabel}</span>
		</button>
	</header>

	<section class="feed" data-density={density} aria-label="Subscription feed">
		{#each feed as item (item.videoId)}
			<article
				class="feed-item"
				class:playing={activeVideoId === item.videoId}
				class:watched={isWatched(item.videoId)}
			>
				{#if density !== 'text'}
					<div class="media-shell">
						{#if activeVideoId === item.videoId}
							<div class="player-frame">
								<YouTubePlayer
									videoId={item.videoId}
									title={item.title}
									onWatched={markWatched}
								/>
							</div>
						{:else}
							<button
								class="thumbnail-button"
								type="button"
								aria-label={`Play ${item.title}`}
								onclick={() => toggleVideo(item.videoId)}
							>
								<img
									alt=""
									class="thumbnail"
									loading="lazy"
									src={getThumbnailUrl(item)}
								/>
							</button>
						{/if}
					</div>
				{/if}

				<div class="copy">
					<h2>{item.title}</h2>
					<div class="meta-line">
						<time datetime={item.publishedAt}>{formatDate(item.publishedAt)}</time>
						<span class="channel">{item.channelName}</span>
					</div>
				</div>
			</article>
		{/each}
	</section>
</div>

<style>
	:global(body) {
		margin: 0;
		background: #000;
		color: #fff;
		font-family:
			'Neue Haas Grotesk Text Pro', 'Avenir Next', 'Helvetica Neue', Helvetica, Arial,
			sans-serif;
	}

	.shell {
		max-width: 1120px;
		margin: 0 auto;
		padding: 20px 18px 64px;
	}

	.topbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 16px;
		margin-bottom: 28px;
	}

	.overline,
	.caption {
		margin: 0;
	}

	.overline {
		font-size: 0.74rem;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: rgba(255, 255, 255, 0.76);
	}

	.caption {
		margin-top: 4px;
		font-size: 0.92rem;
		color: rgba(255, 255, 255, 0.58);
	}

	.density-toggle {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		padding: 0;
		border: 0;
		background: transparent;
		cursor: pointer;
	}

	.density-toggle img {
		display: block;
		width: 32px;
		height: 32px;
	}

	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		white-space: nowrap;
		border: 0;
	}

	.feed {
		display: grid;
		gap: 24px;
	}

	.feed-item {
		display: grid;
		gap: 10px;
		transition: opacity 180ms ease;
	}

	.feed-item.watched {
		opacity: 0.33;
	}

	.media-shell {
		background: #111;
	}

	.thumbnail-button {
		display: block;
		width: 100%;
		padding: 0;
		border: 0;
		background: transparent;
		cursor: pointer;
	}

	.thumbnail,
	.player-frame {
		display: block;
		width: 100%;
		aspect-ratio: 16 / 9;
		object-fit: cover;
		background: #111;
	}

	.copy {
		max-width: 760px;
	}

	h2 {
		margin: 0;
		font-size: clamp(2rem, 4vw, 2.75rem);
		line-height: 0.98;
		letter-spacing: -0.045em;
		font-weight: 700;
	}

	.meta-line {
		display: flex;
		flex-wrap: wrap;
		gap: 12px;
		margin-top: 6px;
		font-size: 0.92rem;
		color: rgba(255, 255, 255, 0.96);
	}

	.channel {
		text-decoration: underline;
		text-underline-offset: 0.14em;
	}

	.feed[data-density='compact'] {
		gap: 16px;
	}

	.feed[data-density='compact'] .feed-item {
		grid-template-columns: minmax(0, 1fr) 124px;
		align-items: start;
		gap: 14px;
	}

	.feed[data-density='compact'] .copy {
		order: 1;
		max-width: none;
	}

	.feed[data-density='compact'] .media-shell {
		order: 2;
	}

	.feed[data-density='compact'] .thumbnail,
	.feed[data-density='compact'] .player-frame {
		aspect-ratio: 1.84 / 1;
	}

	.feed[data-density='compact'] h2 {
		font-size: clamp(1.4rem, 2.2vw, 1.95rem);
	}

	.feed[data-density='compact'] .meta-line {
		font-size: 0.82rem;
		margin-top: 4px;
	}

	.feed[data-density='text'] {
		gap: 18px;
	}

	.feed[data-density='text'] .feed-item {
		gap: 0;
	}

	.feed[data-density='text'] h2 {
		font-size: clamp(1.4rem, 2.4vw, 1.95rem);
		max-width: 22ch;
	}

	.feed[data-density='text'] .meta-line {
		font-size: 0.82rem;
		margin-top: 4px;
	}

	@media (max-width: 700px) {
		.shell {
			padding-inline: 12px;
			padding-top: 14px;
		}

		.topbar {
			align-items: start;
		}

		.feed[data-density='compact'] .feed-item {
			grid-template-columns: minmax(0, 1fr) 96px;
			gap: 10px;
		}

		h2 {
			font-size: 1.9rem;
		}

		.feed[data-density='compact'] h2 {
			font-size: 1.35rem;
		}

		.feed[data-density='text'] h2 {
			font-size: 1.5rem;
		}
	}
</style>
