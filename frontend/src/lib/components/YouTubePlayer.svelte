<script lang="ts">
	import { onMount } from 'svelte';

	const scriptSrc = 'https://www.youtube.com/iframe_api';
	let apiPromise: Promise<YouTubeAPI> | undefined;

	let {
		videoId,
		title,
		onWatched = (_videoId: string) => {}
	}: {
		videoId: string;
		title: string;
		onWatched?: (videoId: string) => void;
	} = $props();

	let host = $state<HTMLElement | null>(null);

	function loadYouTubeApi(): Promise<YouTubeAPI> {
		if (window.YT?.Player) {
			return Promise.resolve(window.YT);
		}

		if (apiPromise) {
			return apiPromise;
		}

		apiPromise = new Promise<YouTubeAPI>((resolve) => {
			const existingHandler = window.onYouTubeIframeAPIReady;

			window.onYouTubeIframeAPIReady = () => {
				existingHandler?.();

				if (!window.YT) {
					throw new Error('YouTube API loaded without window.YT.');
				}

				resolve(window.YT);
			};

			const existingScript = document.querySelector<HTMLScriptElement>(`script[src="${scriptSrc}"]`);
			if (!existingScript) {
				const script = document.createElement('script');
				script.src = scriptSrc;
				script.async = true;
				document.head.appendChild(script);
			}
		});

		return apiPromise;
	}

	onMount(() => {
		if (!host) {
			return;
		}

		let player: PlayerInstance | undefined;
		let markedWatched = false;

		void loadYouTubeApi().then((YT) => {
			if (!host) {
				return;
			}

			player = new YT.Player(host, {
				videoId,
				playerVars: {
					rel: 0,
					modestbranding: 1
				},
				events: {
					onStateChange: (event: PlayerStateEvent) => {
						if (!markedWatched && event.data === YT.PlayerState.PLAYING) {
							markedWatched = true;
							onWatched(videoId);
						}
					}
				}
			});
		});

		return () => {
			player?.destroy();
		};
	});
</script>

<div class="player-shell">
	<div aria-label={title} bind:this={host} class="player-host"></div>
</div>

<style>
	.player-shell,
	.player-host {
		width: 100%;
		height: 100%;
	}

	.player-host :global(iframe) {
		display: block;
		width: 100%;
		height: 100%;
		border: 0;
	}
</style>
