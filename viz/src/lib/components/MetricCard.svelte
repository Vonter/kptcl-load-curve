<script lang="ts">
	import Icon from './Icon.svelte';

	let {
		label,
		value,
		unit = '',
		detail = '',
		icon = 'summary',
		tone = 'green'
	}: {
		label: string;
		value: string;
		unit?: string;
		detail?: string;
		icon?: string;
		tone?: 'green' | 'yellow' | 'red' | 'blue';
	} = $props();
</script>

<article class="metric-card" data-tone={tone}>
	<div class="metric-top">
		<span class="metric-icon"><Icon name={icon} size={18} /></span>
		<span class="metric-label">{label}</span>
	</div>
	<div class="metric-reading">
		<strong>{value}</strong>
		{#if unit}<span>{unit}</span>{/if}
	</div>
	{#if detail}<p>{detail}</p>{/if}
</article>

<style>
	.metric-card {
		min-width: 0;
		border: 1px solid var(--line);
		background: var(--paper);
		padding: 16px 15px 13px;
		box-shadow: var(--panel-shadow);
	}

	.metric-card[data-tone='yellow'] {
		--tone: var(--yellow-dark);
	}

	.metric-card[data-tone='red'] {
		--tone: var(--red);
	}

	.metric-card[data-tone='blue'] {
		--tone: var(--blue);
	}

	.metric-card[data-tone='green'] {
		--tone: var(--green);
	}

	.metric-top {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.metric-icon {
		display: grid;
		place-items: center;
		color: var(--tone);
	}

	.metric-label {
		font-family: var(--font-display);
		font-size: 0.67rem;
		font-weight: 800;
		letter-spacing: 0.105em;
		line-height: 1.2;
		text-transform: uppercase;
		color: var(--muted);
	}

	.metric-reading {
		display: flex;
		align-items: baseline;
		gap: 7px;
		margin-top: 16px;
		font-variant-numeric: tabular-nums;
	}

	.metric-reading strong {
		overflow-wrap: anywhere;
		font-family: var(--font-display);
		font-size: clamp(1.65rem, 3vw, 2.25rem);
		font-weight: 760;
		letter-spacing: -0.045em;
		line-height: 0.95;
		color: var(--ink);
	}

	.metric-reading span {
		font-family: var(--font-unit);
		font-size: 0.68rem;
		font-weight: 750;
		letter-spacing: 0.08em;
		color: var(--muted);
	}

	p {
		margin: 9px 0 0;
		font-family: var(--font-mono);
		font-size: 0.64rem;
		line-height: 1.4;
		color: var(--muted);
	}

	@media (min-width: 881px) {
		.metric-label {
			font-size: 0.75rem;
		}
	}
</style>
