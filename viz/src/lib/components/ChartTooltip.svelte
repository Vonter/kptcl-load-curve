<script lang="ts">
	export type TooltipItem = {
		label: string;
		value: string;
		unit?: string;
		color?: string;
	};

	let {
		open,
		x,
		y,
		title,
		items,
		horizontal = 'right',
		vertical = 'above'
	}: {
		open: boolean;
		x: number;
		y: number;
		title: string;
		items: TooltipItem[];
		horizontal?: 'left' | 'right';
		vertical?: 'above' | 'below';
	} = $props();
</script>

{#if open}
	<div
		class="chart-tooltip {horizontal} {vertical}"
		style={`--tooltip-x:${x}px; --tooltip-y:${y}px`}
		role="tooltip"
	>
		<div class="tooltip-title">{title}</div>
		<div class="tooltip-items">
			{#each items as item (item.label)}
				<div class="tooltip-row">
					<span class="tooltip-label">
						{#if item.color}
							<span class="swatch" style={`--swatch:${item.color}`}></span>
						{/if}
						{item.label}
					</span>
					<strong>
						{item.value}{#if item.unit}<span class="tooltip-unit"> {item.unit}</span>{/if}
					</strong>
				</div>
			{/each}
		</div>
	</div>
{/if}

<style>
	.chart-tooltip {
		position: absolute;
		z-index: 20;
		left: var(--tooltip-x);
		top: var(--tooltip-y);
		width: max-content;
		min-width: 132px;
		max-width: min(230px, calc(100vw - 24px));
		padding: 8px 10px 9px;
		border: 1px solid color-mix(in srgb, var(--ink) 15%, transparent);
		border-radius: 6px;
		background: color-mix(in srgb, var(--paper) 96%, white);
		box-shadow:
			0 8px 24px rgba(29, 42, 36, 0.14),
			0 1px 2px rgba(29, 42, 36, 0.08);
		color: var(--ink);
		font-family: var(--font-mono);
		font-size: 0.65rem;
		line-height: 1.35;
		pointer-events: none;
		animation: tooltip-in 90ms ease-out;
	}

	.chart-tooltip.right {
		transform: translateX(12px);
	}

	.chart-tooltip.left {
		transform: translateX(calc(-100% - 12px));
	}

	.chart-tooltip.above {
		margin-top: -10px;
		translate: 0 -100%;
	}

	.chart-tooltip.below {
		margin-top: 10px;
	}

	.tooltip-title {
		max-width: 210px;
		padding-bottom: 6px;
		border-bottom: 1px solid var(--line);
		font-size: 0.61rem;
		font-weight: 700;
		letter-spacing: 0.025em;
		color: var(--muted-strong);
	}

	.tooltip-items {
		display: grid;
		gap: 4px;
		padding-top: 6px;
	}

	.tooltip-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 16px;
	}

	.tooltip-label {
		display: inline-flex;
		min-width: 0;
		align-items: center;
		gap: 6px;
		color: var(--muted);
	}

	.tooltip-row strong {
		font-size: 0.69rem;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}

	.tooltip-unit {
		font-family: var(--font-unit);
	}

	.swatch {
		width: 7px;
		height: 7px;
		flex: 0 0 auto;
		border-radius: 50%;
		background: var(--swatch);
		box-shadow: 0 0 0 2px color-mix(in srgb, var(--swatch) 18%, transparent);
	}

	@keyframes tooltip-in {
		from {
			opacity: 0;
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.chart-tooltip {
			animation: none;
		}
	}
</style>
