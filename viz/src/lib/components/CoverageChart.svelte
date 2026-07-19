<script lang="ts">
	import { Cell, Plot } from 'svelteplot';
	import ChartTooltip from './ChartTooltip.svelte';

	type SectionCoverage = {
		section: string;
		byYear: number[];
	};
	type CoverageDatum = {
		year: string;
		section: string;
		count: number;
	};

	let {
		years,
		sections,
		labelSection
	}: {
		years: number[];
		sections: SectionCoverage[];
		labelSection: (value: string) => string;
	} = $props();

	let chartData = $derived(
		sections.flatMap((section) =>
			section.byYear.map((count, index) => ({
				year: String(years[index]),
				section: labelSection(section.section),
				count
			}))
		)
	);
	let height = $derived(Math.max(430, sections.length * 25 + 55));
	let chartRoot = $state<HTMLDivElement>();
	let activeDatum = $state<CoverageDatum | null>(null);
	let tooltipX = $state(0);
	let tooltipY = $state(0);
	let tooltipHorizontal = $state<'left' | 'right'>('right');
	let tooltipVertical = $state<'above' | 'below'>('above');
	let pinned = $state(false);

	function showTooltip(event: Event, datum: CoverageDatum, shouldPin = false) {
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
</script>

<svelte:window onpointerdown={dismissPinnedTooltip} />

<div class="coverage-plot" bind:this={chartRoot}>
	<Plot
		{height}
		marginLeft={220}
		marginRight={24}
		marginTop={12}
		marginBottom={44}
		x={{ type: 'band', label: false, domain: years.map(String) }}
		y={{
			type: 'band',
			label: false,
			domain: sections.map((section) => labelSection(section.section)).toReversed()
		}}
		color={{ type: 'linear', scheme: 'greens', domain: [0, 365], legend: false }}
	>
		<Cell
			data={chartData}
			x="year"
			y="section"
			fill="count"
			inset={1}
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
		title={activeDatum?.section ?? ''}
		items={activeDatum
			? [
					{ label: 'Year', value: activeDatum.year },
					{
						label: 'Reports',
						value: activeDatum.count.toLocaleString('en-IN')
					}
				]
			: []}
		horizontal={tooltipHorizontal}
		vertical={tooltipVertical}
	/>
</div>

<style>
	.coverage-plot {
		position: relative;
		min-width: 760px;
		font-family: var(--font-mono);
		font-size: 0.61rem;
		color: var(--muted);
	}

	.coverage-plot :global(figure) {
		margin: 0;
	}
</style>
