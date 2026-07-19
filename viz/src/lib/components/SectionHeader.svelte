<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		code,
		title,
		detail,
		actions,
		alignActions = 'start'
	}: {
		code: string;
		title: string;
		detail?: string;
		actions?: Snippet;
		alignActions?: 'start' | 'center';
	} = $props();
</script>

<header class="section-header" class:centered={alignActions === 'center'}>
	<div class="title-group">
		<span class="section-code">{code}</span>
		<h2>{title}</h2>
	</div>
	{#if actions}
		<div class="actions">{@render actions()}</div>
	{:else if detail}
		<p>{detail}</p>
	{/if}
</header>

<style>
	.section-header {
		display: flex;
		min-width: 0;
		min-height: 34px;
		align-items: flex-start;
		justify-content: space-between;
		gap: 16px;
		margin-bottom: 12px;
		border-bottom: 1px solid var(--line);
		padding-bottom: 11px;
	}

	.title-group {
		display: flex;
		align-items: center;
		gap: 9px;
		min-width: 0;
	}

	.section-code {
		display: grid;
		width: 28px;
		height: 22px;
		place-items: center;
		flex: 0 0 auto;
		background: var(--ink);
		font-family: var(--font-mono);
		font-size: 0.54rem;
		font-weight: 750;
		color: var(--yellow);
	}

	h2 {
		overflow: hidden;
		margin: 0;
		font-family: var(--font-display);
		font-size: 0.93rem;
		font-weight: 750;
		letter-spacing: 0.01em;
		text-overflow: ellipsis;
		white-space: nowrap;
		color: var(--ink);
	}

	p {
		margin: 4px 0 0;
		font-family: var(--font-mono);
		font-size: 0.58rem;
		color: var(--muted);
		white-space: nowrap;
	}

	.actions {
		min-width: 0;
		flex: 0 1 auto;
	}

	.section-header.centered {
		align-items: center;
	}

	@media (max-width: 620px) {
		.section-header {
			align-items: stretch;
			flex-direction: column;
		}

		.section-header.centered {
			align-items: stretch;
		}

		.actions {
			width: 100%;
		}
	}
</style>
