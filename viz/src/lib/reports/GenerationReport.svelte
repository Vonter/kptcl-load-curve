<script lang="ts">
	import { SvelteDate } from 'svelte/reactivity';
	import BarChart from '$lib/components/BarChart.svelte';
	import MetricCard from '$lib/components/MetricCard.svelte';
	import RangeControl from '$lib/components/RangeControl.svelte';
	import ReportHeader from '$lib/components/ReportHeader.svelte';
	import SectionHeader from '$lib/components/SectionHeader.svelte';
	import TablePanel from '$lib/components/TablePanel.svelte';
	import TimeSeriesChart from '$lib/components/TimeSeriesChart.svelte';
	import type {
		ChartDatum,
		DashboardData,
		DateReports,
		ReportSnapshot,
		StationAsset
	} from '$lib/data/types';
	import { chartColors, formatDate, formatNumber, seriesFor, sliceRange } from './reportUtils';

	let {
		dashboard,
		reportSnapshot,
		selectedReportDate,
		dateReports,
		stationRange = $bindable('1Y')
	}: {
		dashboard: DashboardData;
		reportSnapshot: ReportSnapshot;
		selectedReportDate: string;
		dateReports: DateReports;
		stationRange?: string;
	} = $props();

	function stationContributorRows(): ChartDatum[] {
		const names = [
			...reportSnapshot.stations.contributors.other,
			...reportSnapshot.stations.contributors.nce
		];
		const start = new SvelteDate(`${selectedReportDate}T00:00:00`);
		start.setDate(start.getDate() - 365);
		const startDate = start.toISOString().slice(0, 10);
		return Object.entries(dateReports)
			.filter(([date]) => date >= startDate && date <= selectedReportDate)
			.sort(([left], [right]) => left.localeCompare(right))
			.map(([date, report]) => {
				const byStation = new Map(
					report.stations.assets.map((asset) => [asset.station, asset.energy])
				);
				return {
					date,
					...Object.fromEntries(names.map((name) => [name, byStation.get(name) ?? null]))
				};
			});
	}

	let stationHistory = $derived(
		sliceRange(dashboard.stations.history, stationRange, selectedReportDate)
	);
	let nceStations = $derived(
		reportSnapshot.stations.assets.filter((item) =>
			reportSnapshot.stations.contributors.nce.includes(item.station)
		)
	);
	let otherStations = $derived(
		reportSnapshot.stations.assets.filter((item) =>
			reportSnapshot.stations.contributors.other.includes(item.station)
		)
	);
	let contributorHistory = $derived(stationContributorRows());
	let highestGrowth = $derived(
		reportSnapshot.stations.assets
			.filter((asset) => (asset.yearAgoEnergy ?? 0) > 0 && asset.energy !== null)
			.map((asset) => ({
				...asset,
				growth: ((asset.energy! - asset.yearAgoEnergy!) / asset.yearAgoEnergy!) * 100
			}))
			.sort((left, right) => right.growth - left.growth)[0] as
			(StationAsset & { growth: number }) | undefined
	);
</script>

<ReportHeader title="Generation" />

<div class="metric-grid four">
	<MetricCard
		label="Installed capacity"
		value={formatNumber(reportSnapshot.stations.totals.capacity, 0)}
		unit="MW"
		detail="Total installed generation capacity"
		icon="stations"
	/>
	<MetricCard
		label="Maximum output"
		value={formatNumber(reportSnapshot.stations.totals.maximum, 0)}
		unit="MW"
		detail="Generation recorded during peak demand"
		icon="load"
		tone="blue"
	/>
	<MetricCard
		label="Energy supplied"
		value={formatNumber(reportSnapshot.stations.totals.energy, 2)}
		unit="MU"
		detail={`Total supplied on ${formatDate(selectedReportDate)}`}
		icon="summary"
		tone="yellow"
	/>
	<MetricCard
		label="Highest year-over-year growth"
		value={highestGrowth?.station ?? '—'}
		detail={highestGrowth
			? `${highestGrowth.growth > 0 ? '+' : ''}${formatNumber(highestGrowth.growth, 1)}% compared to last year`
			: 'No comparable source data'}
		icon="breaker"
		tone="red"
	/>
</div>

<div class="panel-grid equal">
	<section class="panel">
		<SectionHeader code="02A" title="Total daily energy">
			{#snippet actions()}<RangeControl bind:value={stationRange} />{/snippet}
		</SectionHeader>
		<TimeSeriesChart
			data={stationHistory}
			series={[{ key: 'energy', label: 'Energy', color: chartColors.green, fill: true }]}
			formatX={(value) => formatDate(String(value), true)}
			formatValue={(value) => formatNumber(value, 1)}
			yLabel="Energy (MU)"
			unit="MU"
		/>
	</section>
	<section class="panel">
		<SectionHeader code="02B" title="Largest daily contributors" />
		<div class="chart-grid two contributors-grid">
			<div class="contributor-group">
				<h3>Other sources</h3>
				<BarChart
					data={otherStations}
					labelKey="station"
					valueKey="energy"
					color={chartColors.yellow}
					xLabel="Energy (MU)"
					unit="MU"
				/>
			</div>
			<div class="contributor-group">
				<h3>NCE sources</h3>
				<BarChart
					data={nceStations}
					labelKey="station"
					valueKey="energy"
					color={chartColors.green}
					xLabel="Energy (MU)"
					unit="MU"
				/>
			</div>
		</div>
	</section>
</div>

<section class="panel full-panel">
	<SectionHeader code="02C" title="Contributor variation" />
	<div class="chart-grid two variation-grid">
		<div class="contributor-group">
			<h3>Other sources</h3>
			<TimeSeriesChart
				data={contributorHistory}
				series={seriesFor(reportSnapshot.stations.contributors.other)}
				formatX={(value) => formatDate(String(value), true)}
				formatValue={(value) => formatNumber(value, 1)}
				yLabel="Energy (MU)"
				unit="MU"
			/>
		</div>
		<div class="contributor-group">
			<h3>NCE sources</h3>
			<TimeSeriesChart
				data={contributorHistory}
				series={seriesFor(reportSnapshot.stations.contributors.nce)}
				formatX={(value) => formatDate(String(value), true)}
				formatValue={(value) => formatNumber(value, 1)}
				yLabel="Energy (MU)"
				unit="MU"
			/>
		</div>
	</div>
</section>

<TablePanel code="02D" title="Stations">
	<table>
		<thead
			><tr
				><th>Station</th><th>Capacity</th><th>Daily Energy</th><th>Year-Over-Year</th><th
					>At state max</th
				><th>Day change</th><th>Units gen.</th></tr
			></thead
		>
		<tbody>
			{#each reportSnapshot.stations.assets as asset (asset.station)}
				{@const delta =
					asset.energy !== null && asset.previousEnergy !== null
						? asset.energy - asset.previousEnergy
						: null}
				{@const yearDelta =
					asset.energy !== null && asset.yearAgoEnergy !== null
						? asset.energy - asset.yearAgoEnergy
						: null}
				<tr>
					<td><strong>{asset.station}</strong></td>
					<td>{formatNumber(asset.capacity, 1)} <small class="unit">MW</small></td>
					<td>{formatNumber(asset.energy, 2)} <small class="unit">MU</small></td>
					<td
						><span
							class:positive={(yearDelta ?? 0) > 0}
							class:negative={(yearDelta ?? 0) < 0}
							class="delta"
							>{yearDelta === null
								? '—'
								: `${yearDelta > 0 ? '+' : ''}${formatNumber(yearDelta, 2)}`}</span
						></td
					>
					<td>{formatNumber(asset.generation, 1)} <small class="unit">MW</small></td>
					<td
						><span class:positive={(delta ?? 0) > 0} class:negative={(delta ?? 0) < 0} class="delta"
							>{delta === null ? '—' : `${delta > 0 ? '+' : ''}${formatNumber(delta, 2)}`}</span
						></td
					>
					<td>{formatNumber(asset.units, 0)}</td>
				</tr>
			{/each}
		</tbody>
	</table>
</TablePanel>
