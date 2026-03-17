<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<link rel="manifest" href="/site.webmanifest" />
	<link rel="apple-touch-icon" href="/icon-btn.svg" />
	<meta name="theme-color" content="#000000" />
	<meta name="apple-mobile-web-app-capable" content="yes" />
	<meta name="apple-mobile-web-app-status-bar-style" content="black" />
	<meta name="apple-mobile-web-app-title" content="YouTube Feed" />
	<meta name="application-name" content="YouTube Feed" />
	<meta name="mobile-web-app-capable" content="yes" />
</svelte:head>

{@render children()}
