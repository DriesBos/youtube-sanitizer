// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}

	type PlayerStateEvent = {
		data: number;
	};

	type PlayerInstance = {
		destroy: () => void;
	};

	type YouTubeAPI = {
		Player: new (
			element: HTMLElement,
			options: {
				videoId: string;
				playerVars?: Record<string, string | number>;
				events?: {
					onStateChange?: (event: PlayerStateEvent) => void;
				};
			}
		) => PlayerInstance;
		PlayerState: {
			PLAYING: number;
		};
	};

	interface Window {
		YT?: YouTubeAPI;
		onYouTubeIframeAPIReady?: () => void;
	}
}

export {};
