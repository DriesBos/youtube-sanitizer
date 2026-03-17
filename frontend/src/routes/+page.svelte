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
	const dateFormatter = new Intl.DateTimeFormat('en', {
		month: 'short',
		day: 'numeric',
		year: 'numeric'
	});
	const feed = $derived(data.feed);
	const serverWatchedIds = $derived(
		feed.filter((item: FeedItem) => item.isWatched).map((item: FeedItem) => item.videoId)
	);

	let density = $state<FeedDensity>('full');
	let watchedIds = $state<string[]>([]);

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
		window.localStorage.setItem('feed-density', nextDensity);
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
		return dateFormatter.format(new Date(date));
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
	<header class="hero">
		<div class="hero-copy">
			<p class="eyebrow">YouTube subscriptions</p>
			<h1>Your newest uploads, in chronological order.</h1>
			<p class="lede">
				The frontend is ready for a backend-provided merged feed. Until that exists, this page renders
				a seeded server-side feed with the same shape.
			</p>
		</div>

		<div class="hero-actions">
			<button class="density-toggle" type="button" onclick={cycleDensity}>
				View: {currentDensityLabel}
			</button>
			<p class="helper">Cycle between Full, Compact, and Text only.</p>
		</div>
	</header>

	<section class="feed" data-density={density}>
		{#each feed as item (item.videoId)}
			<article class:watched={isWatched(item.videoId)} class="feed-item">
				<div class="meta">
					<div class="meta-main">
						<p class="channel">{item.channelName}</p>
						<h2>{item.title}</h2>
					</div>
					<div class="meta-side">
						<time datetime={item.publishedAt}>{formatDate(item.publishedAt)}</time>
						{#if item.duration}
							<span>{item.duration}</span>
						{/if}
					</div>
				</div>

				{#if density !== 'text'}
					<div class="player-frame">
						<YouTubePlayer
							videoId={item.videoId}
							title={item.title}
							onWatched={markWatched}
						/>
					</div>
				{/if}

				{#if item.description}
					<p class="description">{item.description}</p>
				{/if}
			</article>
		{/each}
	</section>
</div>

<style>
	:global(body) {
		margin: 0;
		background:
			radial-gradient(circle at top left, rgba(255, 170, 112, 0.24), transparent 32%),
			radial-gradient(circle at top right, rgba(124, 147, 255, 0.18), transparent 24%),
			linear-gradient(180deg, #f7efe6 0%, #efe2d1 48%, #e9dcc8 100%);
		color: #171313;
		font-family:
			'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Palatino, 'Times New Roman',
			serif;
	}

	.shell {
		max-width: 1120px;
		margin: 0 auto;
		padding: 56px 20px 80px;
	}

	.hero {
		display: grid;
		grid-template-columns: minmax(0, 1fr) auto;
		gap: 24px;
		align-items: end;
		margin-bottom: 32px;
	}

	.eyebrow {
		margin: 0 0 10px;
		font-size: 0.78rem;
		letter-spacing: 0.18em;
		text-transform: uppercase;
		color: #7e4d2d;
	}

	h1 {
		margin: 0;
		font-size: clamp(2.5rem, 7vw, 5.4rem);
		line-height: 0.94;
		max-width: 10ch;
	}

	.lede {
		margin: 18px 0 0;
		max-width: 54ch;
		font-size: 1.05rem;
		line-height: 1.6;
		color: rgba(23, 19, 19, 0.74);
	}

	.hero-actions {
		display: grid;
		justify-items: end;
		gap: 10px;
	}

	.density-toggle {
		border: 0;
		border-radius: 999px;
		padding: 14px 18px;
		background: #171313;
		color: #f7efe6;
		font: inherit;
		cursor: pointer;
		box-shadow: 0 14px 32px rgba(23, 19, 19, 0.16);
	}

	.helper {
		margin: 0;
		font-size: 0.9rem;
		color: rgba(23, 19, 19, 0.62);
	}

	.feed {
		display: grid;
		gap: 18px;
	}

	.feed-item {
		padding: 18px;
		border: 1px solid rgba(23, 19, 19, 0.1);
		border-radius: 28px;
		background: rgba(255, 252, 247, 0.72);
		backdrop-filter: blur(16px);
		box-shadow: 0 16px 36px rgba(78, 51, 31, 0.08);
		transition:
			opacity 180ms ease,
			transform 180ms ease,
			box-shadow 180ms ease;
	}

	.feed-item:hover {
		transform: translateY(-2px);
		box-shadow: 0 20px 44px rgba(78, 51, 31, 0.12);
	}

	.feed-item.watched {
		opacity: 0.33;
	}

	.meta {
		display: flex;
		justify-content: space-between;
		gap: 18px;
		margin-bottom: 16px;
	}

	.meta-main h2 {
		margin: 6px 0 0;
		font-size: clamp(1.25rem, 2vw, 1.65rem);
		line-height: 1.18;
	}

	.channel {
		margin: 0;
		font-size: 0.9rem;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #7f5a40;
	}

	.meta-side {
		display: grid;
		gap: 4px;
		text-align: right;
		white-space: nowrap;
		font-size: 0.92rem;
		color: rgba(23, 19, 19, 0.62);
	}

	.player-frame {
		aspect-ratio: 16 / 9;
		overflow: hidden;
		border-radius: 22px;
		background: #0f0f0f;
	}

	.description {
		margin: 14px 0 0;
		max-width: 68ch;
		line-height: 1.6;
		color: rgba(23, 19, 19, 0.72);
	}

	.feed[data-density='compact'] .feed-item {
		display: grid;
		grid-template-columns: minmax(0, 1.2fr) minmax(280px, 0.8fr);
		gap: 18px;
		align-items: start;
	}

	.feed[data-density='compact'] .meta,
	.feed[data-density='compact'] .description {
		grid-column: 1;
	}

	.feed[data-density='compact'] .player-frame {
		grid-column: 2;
		grid-row: 1 / span 2;
	}

	.feed[data-density='text'] .feed-item {
		padding: 18px 22px;
	}

	.feed[data-density='text'] .meta {
		margin-bottom: 8px;
	}

	@media (max-width: 860px) {
		.hero {
			grid-template-columns: 1fr;
			align-items: start;
		}

		.hero-actions {
			justify-items: start;
		}

		.feed[data-density='compact'] .feed-item {
			grid-template-columns: 1fr;
		}

		.feed[data-density='compact'] .meta,
		.feed[data-density='compact'] .description,
		.feed[data-density='compact'] .player-frame {
			grid-column: auto;
			grid-row: auto;
		}
	}

	@media (max-width: 640px) {
		.shell {
			padding-inline: 14px;
			padding-top: 40px;
		}

		.feed-item {
			padding: 16px;
			border-radius: 22px;
		}

		.meta {
			flex-direction: column;
		}

		.meta-side {
			text-align: left;
		}
	}
</style>
