<script lang="ts">
	import { BarX, Plot } from 'svelteplot';
	import ChartTooltip from './ChartTooltip.svelte';

	type Datum = Record<string, string | number | null>;

	let {
		data,
		labelKey,
		valueKey,
		secondaryKey,
		color = 'var(--green)',
		xLabel = '',
		unit = '',
		formatValue = (value: number) => value.toLocaleString('en-IN', { maximumFractionDigits: 2 })
	}: {
		data: Datum[];
		labelKey: string;
		valueKey: string;
		secondaryKey?: string;
		color?: string;
		xLabel?: string;
		unit?: string;
		formatValue?: (value: number) => string;
	} = $props();

	let chartData = $derived(data.filter((item) => typeof item[valueKey] === 'number').toReversed());
	let chartHeight = $derived(Math.max(180, chartData.length * 30 + 42));
	let chartRoot = $state<HTMLDivElement>();
	let chartWidth = $state(320);
	let marginLeft = $derived(chartWidth < 360 ? 96 : chartWidth < 520 ? 118 : 150);
	let marginRight = $derived(chartWidth < 520 ? 12 : 52);
	let activeDatum = $state<Datum | null>(null);
	let tooltipX = $state(0);
	let tooltipY = $state(0);
	let tooltipHorizontal = $state<'left' | 'right'>('right');
	let tooltipVertical = $state<'above' | 'below'>('above');
	let pinned = $state(false);

	function showTooltip(event: Event, datum: Datum, shouldPin = false) {
		if (!(event instanceof PointerEvent) || !chartRoot) return;
		const bounds = chartRoot.getBoundingClientRect();
		tooltipX = event.clientX - bounds.left;
		tooltipY = event.clientY - bounds.top;
		tooltipHorizontal = tooltipX > bounds.width / 2 ? 'left' : 'right';
		tooltipVertical = tooltipY > 90 ? 'above' : 'below';
		activeDatum = datum;
		if (shouldPin && event.pointerType !== 'mouse') pinned = true;
	}

	function hideTooltip() {
		if (!pinned) activeDatum = null;
	}

	function dismissPinnedTooltip(event: PointerEvent) {
		if (pinned && chartRoot && !chartRoot.contains(event.target as Node)) {
			pinned = false;
			activeDatum = null;
		}
	}

	function formatLabel(value: unknown): string {
		const label = String(value);
		const limit = chartWidth < 360 ? 12 : chartWidth < 520 ? 16 : 24;
		return label.length > limit ? `${label.slice(0, limit - 1)}…` : label;
	}
</script>

<svelte:window onpointerdown={dismissPinnedTooltip} />

{#if chartData.length}
	<div class="bar-plot" bind:this={chartRoot} bind:clientWidth={chartWidth}>
		<Plot
			height={chartHeight}
			{marginLeft}
			{marginRight}
			marginTop={6}
			marginBottom={xLabel ? 46 : 34}
			x={{
				label: xLabel || false,
				grid: true,
				tickFormat: (value: unknown) => formatValue(Number(value))
			}}
			y={{
				label: false,
				domain: chartData.map((item) => item[labelKey]),
				tickFormat: formatLabel
			}}
		>
			<BarX
				data={chartData}
				x={valueKey}
				y={labelKey}
				fill={color}
				inset={2}
				cursor="pointer"
				onpointerenter={(event, row) => showTooltip(event, row)}
				onpointermove={(event, row) => showTooltip(event, row)}
				onpointerleave={hideTooltip}
				onpointerdown={(event, row) => showTooltip(event, row, true)}
			/>
		</Plot>
		<ChartTooltip
			open={activeDatum !== null}
			x={tooltipX}
			y={tooltipY}
			title={activeDatum ? String(activeDatum[labelKey]) : ''}
			items={activeDatum
				? [
						{
							label: 'Value',
							value: formatValue(activeDatum[valueKey] as number),
							unit,
							color
						},
						...(secondaryKey && typeof activeDatum[secondaryKey] === 'number'
							? [
									{
										label: 'Secondary',
										value: formatValue(activeDatum[secondaryKey] as number)
									}
								]
							: [])
					]
				: []}
			horizontal={tooltipHorizontal}
			vertical={tooltipVertical}
		/>
	</div>
{:else}
	<div class="empty">No contributors reported.</div>
{/if}

<style>
	.bar-plot {
		position: relative;
		width: 100%;
		max-width: 100%;
		min-width: 0;
		overflow: hidden;
		font-family: var(--font-mono);
		font-size: 0.62rem;
		color: var(--muted);
	}

	.bar-plot :global(figure) {
		width: 100%;
		min-width: 0;
		margin: 0;
	}

	.bar-plot :global(svg) {
		display: block;
		max-width: 100%;
	}

	.bar-plot :global(.axis-x-title),
	.bar-plot :global(.axis-y-title) {
		font-family: var(--font-unit);
	}

	.empty {
		display: grid;
		min-height: 180px;
		place-items: center;
		font-family: var(--font-mono);
		font-size: 0.68rem;
		color: var(--muted);
	}
</style>
