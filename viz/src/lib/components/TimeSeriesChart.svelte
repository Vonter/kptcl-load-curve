<script lang="ts">
	import { AreaY, Dot, Line, Plot, Pointer, RuleX, RuleY } from 'svelteplot';
	import ChartTooltip from './ChartTooltip.svelte';

	type Datum = Record<string, string | number | null | Date>;
	type Series = {
		key: string;
		label: string;
		color: string;
		dashed?: boolean;
		fill?: boolean;
	};
	type InteractionDatum = Datum & {
		__seriesKey: string;
		__seriesLabel: string;
		__seriesColor: string;
		__value: number;
	};
	type Band = {
		lowerKey: string;
		upperKey: string;
		color: string;
		opacity?: number;
	};

	let {
		data,
		series,
		xKey = 'date',
		height = 300,
		yMin,
		yMax,
		yLabel = '',
		xLabel = '',
		xTicks,
		unit = '',
		band,
		formatValue = (value: number) => value.toLocaleString('en-IN', { maximumFractionDigits: 1 }),
		formatX = (value: string | number) => String(value),
		target
	}: {
		data: Datum[];
		series: Series[];
		xKey?: string;
		height?: number;
		yMin?: number;
		yMax?: number;
		yLabel?: string;
		xLabel?: string;
		xTicks?: (string | number | Date)[];
		unit?: string;
		band?: Band;
		formatValue?: (value: number) => string;
		formatX?: (value: string | number) => string;
		target?: { min: number; max: number; color?: string };
	} = $props();

	let hidden = $state<string[]>([]);
	let chartRoot = $state<HTMLDivElement>();
	let chartWidth = $state(500);
	let marginLeft = $derived(chartWidth < 420 ? (yLabel ? 66 : 52) : yLabel ? 78 : 72);
	let marginRight = $derived(chartWidth < 420 ? 10 : 18);
	let tickSpacing = $derived(chartWidth < 420 ? 85 : 135);
	let activePoint = $state<InteractionDatum | null>(null);
	let tooltipX = $state(0);
	let tooltipY = $state(0);
	let tooltipHorizontal = $state<'left' | 'right'>('right');
	let tooltipVertical = $state<'above' | 'below'>('above');
	let pinned = $state(false);
	let visibleSeries = $derived(series.filter((item) => !hidden.includes(item.key)));
	let plotData = $derived(
		data.map((row): Datum => ({
			...row,
			__x:
				xKey === 'date' && typeof row[xKey] === 'string'
					? new Date(`${row[xKey]}T00:00:00`)
					: row[xKey]
		}))
	);
	let interactionData = $derived(
		plotData.flatMap((row) =>
			visibleSeries.flatMap((item): InteractionDatum[] => {
				const value = row[item.key];
				return typeof value === 'number' && Number.isFinite(value)
					? [
							{
								...row,
								__seriesKey: item.key,
								__seriesLabel: item.label,
								__seriesColor: item.color,
								__value: value
							}
						]
					: [];
			})
		)
	);
	let activeRow = $derived(activePoint ?? plotData.at(-1));
	let observedValues = $derived(
		plotData.flatMap((row) =>
			visibleSeries
				.map((item) => row[item.key])
				.filter((value): value is number => typeof value === 'number' && Number.isFinite(value))
		)
	);
	let yDomain = $derived(
		yMin === undefined && yMax === undefined
			? undefined
			: [
					yMin ?? (observedValues.length ? Math.min(...observedValues) : 0),
					yMax ?? (observedValues.length ? Math.max(...observedValues) : 1)
				]
	);
	let displayValue = $derived((value: number) => formatValue(value));

	function originalX(value: unknown): string | number {
		if (value instanceof Date) return value.toISOString().slice(0, 10);
		return value as string | number;
	}

	function toggle(key: string) {
		hidden = hidden.includes(key) ? hidden.filter((item) => item !== key) : [...hidden, key];
		if (activePoint?.__seriesKey === key) activePoint = null;
	}

	function positionTooltip(event: PointerEvent) {
		if (!chartRoot) return;
		const bounds = chartRoot.getBoundingClientRect();
		tooltipX = event.clientX - bounds.left;
		tooltipY = event.clientY - bounds.top;
		tooltipHorizontal = tooltipX > bounds.width / 2 ? 'left' : 'right';
		tooltipVertical = tooltipY > 110 ? 'above' : 'below';
	}

	function updatePointer(rows: InteractionDatum[]) {
		if (rows[0]) activePoint = rows[0];
		else if (!pinned) activePoint = null;
	}

	function handlePointerDown(event: PointerEvent) {
		positionTooltip(event);
		if (event.pointerType === 'mouse' || !chartRoot) return;

		pinned = true;
		chartRoot.querySelector<HTMLElement>('.plot-body')?.dispatchEvent(
			new PointerEvent('pointermove', {
				bubbles: true,
				clientX: event.clientX,
				clientY: event.clientY,
				pointerId: event.pointerId,
				pointerType: event.pointerType,
				isPrimary: event.isPrimary
			})
		);
	}

	function dismissPinnedTooltip(event: PointerEvent) {
		if (pinned && chartRoot && !chartRoot.contains(event.target as Node)) {
			pinned = false;
			activePoint = null;
		}
	}
</script>

<svelte:window onpointerdown={dismissPinnedTooltip} />

<div class="chart-shell">
	<div class="chart-readout">
		<span class="readout-time">{activeRow ? formatX(originalX(activeRow.__x)) : 'No data'}</span>
		<div class="legend">
			{#each series as item (item.key)}
				<button
					type="button"
					class:muted={hidden.includes(item.key)}
					onclick={() => toggle(item.key)}
				>
					<span class="key" style={`--series-color:${item.color}`}></span>
					<span>{item.label}</span>
					<strong>
						{activeRow && typeof activeRow[item.key] === 'number'
							? displayValue(activeRow[item.key] as number)
							: '—'}
						{#if unit}<span class="unit"> {unit}</span>{/if}
					</strong>
				</button>
			{/each}
		</div>
	</div>

	{#if plotData.length}
		<div
			class="plot-wrap"
			bind:this={chartRoot}
			bind:clientWidth={chartWidth}
			role="group"
			aria-label="Interactive time series chart"
			onpointermove={positionTooltip}
			onpointerdown={handlePointerDown}
		>
			<Plot
				{height}
				grid
				{marginLeft}
				{marginRight}
				marginTop={yLabel ? 30 : 12}
				marginBottom={42}
				x={{
					label: xLabel || false,
					tickSpacing,
					ticks: xTicks,
					tickFormat: (value: unknown) => formatX(originalX(value))
				}}
				y={{
					label: yLabel || false,
					domain: yDomain,
					nice: yMin === undefined && yMax === undefined,
					tickFormat: (value: unknown) => formatValue(Number(value))
				}}
			>
				{#if band}
					<AreaY
						data={plotData}
						x="__x"
						y1={band.lowerKey}
						y2={band.upperKey}
						fill={band.color}
						fillOpacity={band.opacity ?? 0.12}
					/>
				{/if}
				{#if target}
					<RuleY
						data={[target.min, target.max]}
						y={(value) => value}
						stroke={target.color ?? '#1d7551'}
						strokeOpacity={0.45}
						strokeDasharray="5 4"
					/>
				{/if}
				{#each visibleSeries as item (item.key)}
					{#if item.fill}
						<AreaY data={plotData} x="__x" y={item.key} fill={item.color} fillOpacity={0.1} />
					{/if}
					<Line
						data={plotData}
						x="__x"
						y={item.key}
						stroke={item.color}
						strokeWidth={2}
						strokeDasharray={item.dashed ? '6 4' : undefined}
					/>
				{/each}
				<RuleX
					data={activePoint ? [activePoint] : []}
					x="__x"
					stroke="var(--ink)"
					strokeOpacity={0.22}
				/>
				{#each visibleSeries as item (item.key)}
					<Dot
						data={activePoint?.__seriesKey === item.key ? [activePoint] : []}
						x="__x"
						y="__value"
						r={4}
						fill={item.color}
						stroke="var(--paper)"
						strokeWidth={2}
					/>
				{/each}
				<Pointer
					data={interactionData}
					x="__x"
					y="__value"
					onupdate={(rows) => updatePointer(rows as InteractionDatum[])}
					maxDistance={40}
				/>
			</Plot>
			<ChartTooltip
				open={activePoint !== null}
				x={tooltipX}
				y={tooltipY}
				title={activePoint ? formatX(originalX(activePoint.__x)) : ''}
				items={activePoint
					? [
							{
								label: activePoint.__seriesLabel,
								value: displayValue(activePoint.__value),
								unit,
								color: activePoint.__seriesColor
							}
						]
					: []}
				horizontal={tooltipHorizontal}
				vertical={tooltipVertical}
			/>
		</div>
	{:else}
		<div class="empty">No readings in this interval.</div>
	{/if}
</div>

<style>
	.chart-shell {
		width: 100%;
		max-width: 100%;
		min-width: 0;
	}

	.chart-readout {
		display: flex;
		min-height: 34px;
		align-items: flex-start;
		flex-wrap: wrap;
		gap: 5px 16px;
		margin: 0 9px 3px 72px;
	}

	.readout-time {
		padding-top: 5px;
		font-family: var(--font-mono);
		font-size: 0.65rem;
		font-weight: 700;
		letter-spacing: 0.03em;
		color: var(--muted);
		white-space: nowrap;
	}

	.legend {
		display: flex;
		flex-wrap: wrap;
		justify-content: flex-start;
		gap: 4px 13px;
	}

	.legend button {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		border: 0;
		background: transparent;
		padding: 3px 0;
		font-family: var(--font-mono);
		font-size: 0.61rem;
		color: var(--muted);
		cursor: pointer;
	}

	.legend button strong {
		font-size: 0.65rem;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}

	.unit {
		font-family: var(--font-unit);
	}

	.legend button.muted {
		opacity: 0.38;
	}

	.key {
		width: 14px;
		height: 3px;
		background: var(--series-color);
	}

	.plot-wrap {
		position: relative;
		width: 100%;
		max-width: 100%;
		min-width: 0;
		overflow: hidden;
		color: var(--muted);
		font-family: var(--font-mono);
		font-size: 0.64rem;
	}

	.plot-wrap :global(figure) {
		width: 100%;
		min-width: 0;
		margin: 0;
	}

	.plot-wrap :global(svg) {
		display: block;
		max-width: 100%;
	}

	.plot-wrap :global(.axis-x-title),
	.plot-wrap :global(.axis-y-title) {
		font-family: var(--font-unit);
	}

	.empty {
		display: grid;
		height: 300px;
		place-items: center;
		font-family: var(--font-mono);
		font-size: 0.68rem;
		color: var(--muted);
	}

	@media (max-width: 620px) {
		.chart-readout {
			align-items: stretch;
			flex-direction: column;
			gap: 5px;
			margin-left: 4px;
		}

		.legend {
			justify-content: flex-start;
		}
	}
</style>
