<script lang="ts">
	import './layout.css';
	import '@fontsource-variable/mona-sans/wght.css';
	import '@fontsource/caladea/400.css';
	import '@fontsource/caladea/700.css';
	import '@fontsource/space-mono/400.css';
	import '@fontsource/space-mono/700.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>
{@render children()}
