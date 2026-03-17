<script lang="ts">
	import { onMount } from 'svelte';
	import YouTubePlayer from '$lib/components/YouTubePlayer.svelte';
	import type { AuthStatus, FeedDensity, FeedItem } from '$lib/types';

	let { data } = $props<{
		data: {
			apiBase?: string;
			authStatus: AuthStatus;
			feed: FeedItem[];
		};
	}>();

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
	const authStatus = $derived(data.authStatus);
	const connectUrl = $derived(data.apiBase ? `${data.apiBase}/api/auth/google/start` : '');

	let density = $state<FeedDensity>('full');
	let watchedIds = $state<string[]>([]);
	let syncing = $state(false);
	let syncError = $state('');
	let authMessage = $state('');

	const currentDensityLabel = $derived(densityLabels[density]);

	onMount(() => {
		const storedDensity = window.localStorage.getItem('feed-density');
		const storedWatched = window.localStorage.getItem('watched-video-ids');
		const params = new URLSearchParams(window.location.search);

		if (storedDensity === 'full' || storedDensity === 'compact' || storedDensity === 'text') {
			density = storedDensity;
		}

		if (storedWatched) {
			const parsed = JSON.parse(storedWatched) as string[];
			watchedIds = [...new Set(parsed)];
		}

		const auth = params.get('auth');
		if (auth === 'connected') {
			authMessage = 'YouTube connected. Run sync if your feed has not refreshed yet.';
		} else if (auth) {
			authMessage = `Authentication returned: ${auth}.`;
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

		void fetch(`/api/feed/${videoId}/watched`, {
			method: 'POST'
		}).catch(() => {
			// Local state is enough to keep the UI responsive if the backend is unavailable.
		});
	}

	async function runSync() {
		syncing = true;
		syncError = '';

		try {
			const response = await fetch('/api/sync', { method: 'POST' });
			if (!response.ok) {
				const payload = await response.json().catch(() => ({ detail: 'Sync failed.' }));
				syncError = payload.detail ?? 'Sync failed.';
				return;
			}

			window.location.reload();
		} catch (error) {
			syncError = 'Sync failed.';
		} finally {
			syncing = false;
		}
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

		<div class="controls">
			{#if authStatus.configured}
				{#if authStatus.connected}
					<button class="action-button" type="button" onclick={runSync} disabled={syncing}>
						{syncing ? 'Syncing...' : 'Sync'}
					</button>
				{:else if connectUrl}
					<a class="action-button link-button" href={connectUrl}>Connect YouTube</a>
				{/if}
			{/if}

			<button class="density-toggle" type="button" onclick={cycleDensity}>
				<img alt="" aria-hidden="true" src="/icon-btn.svg" />
				<span class="sr-only">Cycle viewing mode. Current mode: {currentDensityLabel}</span>
			</button>
		</div>
	</header>

	{#if !authStatus.configured}
		<p class="status-banner warning">
			Add `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` to the backend to enable real YouTube data.
		</p>
	{:else if !authStatus.connected}
		<p class="status-banner">Connect your Google account to replace the demo feed with your subscriptions.</p>
	{:else}
		<p class="status-banner">
			Connected. {authStatus.subscriptionCount} subscriptions cached, {authStatus.videoCount} videos in the
			current feed snapshot.
		</p>
	{/if}

	{#if authMessage}
		<p class="status-banner">{authMessage}</p>
	{/if}

	{#if syncError}
		<p class="status-banner warning">{syncError}</p>
	{/if}

	<section class="feed" data-density={density} aria-label="Subscription feed">
		{#each feed as item (item.videoId)}
			<article class="feed-item" class:watched={isWatched(item.videoId)}>
				{#if density !== 'text'}
					<div class="media-shell">
						<div class="player-frame">
							<YouTubePlayer
								videoId={item.videoId}
								title={item.title}
								onWatched={markWatched}
							/>
						</div>
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

	.controls {
		display: flex;
		align-items: center;
		gap: 12px;
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

	.action-button {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-height: 32px;
		padding: 0 12px;
		border: 1px solid rgba(255, 255, 255, 0.24);
		background: transparent;
		color: #fff;
		font: inherit;
		text-decoration: none;
		cursor: pointer;
	}

	.action-button:disabled {
		opacity: 0.55;
		cursor: progress;
	}

	.link-button {
		white-space: nowrap;
	}

	.density-toggle img {
		display: block;
		width: 32px;
		height: 32px;
	}

	.status-banner {
		margin: 0 0 18px;
		padding: 10px 12px;
		border: 1px solid rgba(255, 255, 255, 0.14);
		color: rgba(255, 255, 255, 0.82);
		font-size: 0.92rem;
	}

	.status-banner.warning {
		border-color: rgba(255, 196, 0, 0.42);
		color: #ffd665;
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

	.player-frame {
		display: block;
		width: 100%;
		aspect-ratio: 16 / 9;
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
			flex-direction: column;
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
