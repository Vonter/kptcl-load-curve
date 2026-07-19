<script lang="ts">
	let {
		value = $bindable(),
		options = ['30D', '1Y', '5Y', 'ALL']
	}: { value: string; options?: string[] } = $props();
</script>

<div class="range-control" aria-label="Chart date range">
	{#each options as option (option)}
		<button class:active={value === option} type="button" onclick={() => (value = option)}
			>{option}</button
		>
	{/each}
</div>

<style>
	.range-control {
		display: inline-flex;
		align-items: center;
		border: 1px solid var(--line-strong);
		background: var(--paper-deep);
		padding: 2px;
	}

	button {
		border: 0;
		background: transparent;
		padding: 6px 9px;
		font-family: var(--font-mono);
		font-size: 0.62rem;
		font-weight: 750;
		letter-spacing: 0.04em;
		color: var(--muted);
		cursor: pointer;
	}

	button:hover {
		color: var(--ink);
	}

	button.active {
		background: var(--ink);
		color: var(--paper);
	}
</style>
