<script lang="ts">
	import Icon from './Icon.svelte';

	let {
		inline = false,
		error = '',
		title = 'Dashboard data unavailable'
	}: { inline?: boolean; error?: string; title?: string } = $props();
</script>

<div class:inline class:error class="load-state">
	{#if error}
		{#if !inline}<Icon name="outages" size={28} />{/if}
		<strong>{title}</strong><span>{error}</span>
	{:else}
		<span class="spinner"></span><strong>Loading data...</strong>
	{/if}
</div>

<style>
	.load-state {
		display: grid;
		min-height: calc(100vh - 74px);
		place-content: center;
		place-items: center;
		gap: 9px;
		font-family: var(--font-mono);
		color: var(--muted);
	}
	.load-state.inline {
		min-height: 360px;
	}
	.load-state.error {
		color: var(--red);
	}
	.load-state:not(.inline) strong {
		font-family: var(--font-display);
		font-size: 1rem;
		letter-spacing: 0.04em;
		color: var(--ink);
	}
	.load-state:not(.inline) span:not(.spinner) {
		font-size: 0.67rem;
	}
	.spinner {
		width: 26px;
		height: 26px;
		border: 3px solid var(--line);
		border-top-color: var(--yellow-dark);
		border-radius: 50%;
		animation: spin 800ms linear infinite;
	}
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>
