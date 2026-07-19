<script lang="ts">
	import type { Snippet } from 'svelte';
	import SectionHeader from './SectionHeader.svelte';

	let {
		code,
		title,
		detail,
		actions,
		alignActions = 'start',
		children
	}: {
		code: string;
		title: string;
		detail?: string;
		actions?: Snippet;
		alignActions?: 'start' | 'center';
		children: Snippet;
	} = $props();
</script>

<section class="table-panel">
	<SectionHeader {code} {title} {detail} {actions} {alignActions} />
	<div class="table-scroll">{@render children()}</div>
</section>

<style>
	.table-panel {
		min-width: 0;
		margin-top: var(--report-section-gap);
		border: 1px solid var(--line);
		background: var(--paper);
		padding: 16px 17px 8px;
		box-shadow: var(--panel-shadow);
	}

	.table-scroll {
		max-width: 100%;
		overflow-x: auto;
		overscroll-behavior-inline: contain;
		-webkit-overflow-scrolling: touch;
	}

	.table-scroll :global(table) {
		width: 100%;
		max-width: 100%;
		border-collapse: collapse;
		font-variant-numeric: tabular-nums;
		text-align: left;
	}

	.table-scroll :global(th) {
		border-bottom: 2px solid var(--ink);
		padding: 9px 11px;
		font-family: var(--font-display);
		font-size: 0.64rem;
		font-weight: 750;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--muted);
		white-space: nowrap;
	}

	.table-scroll :global(td) {
		border-bottom: 1px solid var(--line);
		padding: 10px 11px;
		font-family: var(--font-mono);
		font-size: 0.65rem;
		line-height: 1.45;
		color: var(--muted-strong);
		vertical-align: top;
	}

	.table-scroll :global(tbody tr:hover) {
		background: color-mix(in srgb, var(--yellow) 7%, transparent);
	}

	.table-scroll :global(td strong) {
		display: block;
		font-family: var(--font-body);
		font-size: 0.73rem;
		font-weight: 680;
		color: var(--ink);
	}

	.table-scroll :global(td small) {
		display: block;
		margin-top: 2px;
		font-family: var(--font-mono);
		font-size: 0.54rem;
		text-transform: uppercase;
		color: var(--muted);
	}

	.table-scroll :global(.unit) {
		font-family: var(--font-unit);
	}

	@media (max-width: 620px) {
		.table-panel {
			padding: 13px 10px 8px;
		}
	}
</style>
