<script lang="ts">
	let { name, size = 20 }: { name: string; size?: number } = $props();
</script>

<svg
	width={size}
	height={size}
	viewBox="0 0 24 24"
	fill="none"
	stroke="currentColor"
	stroke-width="1.75"
	stroke-linecap="round"
	stroke-linejoin="round"
	aria-hidden="true"
>
	{#if name === 'load'}
		<path d="M3 12h3l2.1-6 3.8 12 2.4-8 1.7 2h5" />
	{:else if name === 'stations'}
		<path d="M5 21V8h5v13M14 21V3h5v18M3 21h18" />
		<path d="M7 11h1M7 15h1M16 7h1M16 11h1M16 15h1" />
	{:else if name === 'reservoirs'}
		<path d="M12 3C9.2 7.1 6 10.3 6 14a6 6 0 0 0 12 0c0-3.7-3.2-6.9-6-11Z" />
		<path d="M9 15.5c1.2 1 2.2 1.3 3 1.3 1.1 0 2.1-.4 3-1.3" />
	{:else if name === 'outages'}
		<path d="m13 2-7 11h6l-1 9 7-12h-6l1-8Z" />
	{:else if name === 'summary'}
		<circle cx="12" cy="12" r="8" />
		<path d="M12 12 16.5 8M12 5v2M5 12h2M17 12h2M8.3 8.3l-1.4-1.4M15.7 8.3l1.4-1.4" />
	{:else if name === 'sections'}
		<path d="M4 5h16v14H4zM8 5v14M4 10h16M4 14.5h16" />
	{:else if name === 'historical'}
		<path d="M4 19V5M4 19h16" />
		<path d="m7 15 3-4 3 2 5-7" />
		<path d="M15 6h3v3" />
	{:else if name === 'calendar'}
		<path d="M5 4h14a2 2 0 0 1 2 2v14H3V6a2 2 0 0 1 2-2ZM7 2v4M17 2v4M3 9h18" />
	{:else if name === 'download'}
		<path d="M12 3v12m0 0 4-4m-4 4-4-4M4 20h16" />
	{:else if name === 'breaker'}
		<circle cx="7" cy="12" r="3" />
		<circle cx="17" cy="12" r="3" />
		<path d="m9.5 10.2 5-5M2 12h2M20 12h2" />
	{:else if name === 'clock'}
		<circle cx="12" cy="12" r="9" />
		<path d="M12 7v5l3 2" />
	{:else if name === 'search'}
		<circle cx="10.5" cy="10.5" r="6.5" />
		<path d="m16 16 5 5" />
	{:else if name === 'workbook'}
		<path d="M7 3h7l5 5v13H7z" />
		<path d="M14 3v5h5" />
		<path d="M10.5 12.5h6M10.5 16.5h6M13.5 12.5v4" />
	{:else if name === 'github'}
		<path
			d="M12 2.8a9.3 9.3 0 0 0-2.9 18.1c.5.1.6-.2.6-.5v-1.8c-2.7.6-3.3-1.2-3.3-1.2-.4-1.1-1.1-1.4-1.1-1.4-.9-.6.1-.6.1-.6 1 0 1.5 1 1.5 1 .9 1.5 2.3 1.1 2.9.8.1-.7.4-1.1.6-1.3-2.2-.2-4.5-1.1-4.5-4.6 0-1 .4-1.9 1-2.5-.1-.3-.4-1.3.1-2.5 0 0 .8-.3 2.6 1a9 9 0 0 1 4.8 0c1.8-1.2 2.6-1 2.6-1 .5 1.2.2 2.2.1 2.5.6.6 1 1.5 1 2.5 0 3.6-2.3 4.4-4.5 4.6.4.3.7.9.7 1.7v2.6c0 .4.2.6.7.5A9.3 9.3 0 0 0 12 2.8Z"
			fill="currentColor"
			stroke="none"
		/>
	{:else}
		<circle cx="12" cy="12" r="8" />
		<path d="M12 8v4m0 4h.01" />
	{/if}
</svg>
