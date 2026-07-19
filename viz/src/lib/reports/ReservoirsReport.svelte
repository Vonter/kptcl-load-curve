<script lang="ts">
	import MetricCard from '$lib/components/MetricCard.svelte';
	import RangeControl from '$lib/components/RangeControl.svelte';
	import ReportHeader from '$lib/components/ReportHeader.svelte';
	import SectionHeader from '$lib/components/SectionHeader.svelte';
	import TimeSeriesChart from '$lib/components/TimeSeriesChart.svelte';
	import type { DashboardData, ReservoirDay } from '$lib/data/types';
	import { chartColors, formatDate, formatNumber, oneYearAgo, sliceRange } from './reportUtils';

	let {
		dashboard,
		selectedReportDate,
		reservoirRange = $bindable('1Y')
	}: {
		dashboard: DashboardData;
		selectedReportDate: string;
		reservoirRange?: string;
	} = $props();

	function reservoirRows(name: string): ReservoirDay[] {
		return sliceRange(
			dashboard.reservoirs.history.filter((row) => row.reservoir === name),
			reservoirRange,
			selectedReportDate
		);
	}

	let allReservoirLatest = $derived(
		dashboard.reservoirs.history.filter((row) => row.date === selectedReportDate)
	);
	let previousYearDate = $derived(oneYearAgo(selectedReportDate));
</script>

<ReportHeader title="Reservoirs" />

<div class="reservoir-list">
	{#each allReservoirLatest as reservoir (reservoir.reservoir)}
		{@const history = reservoirRows(reservoir.reservoir)}
		<section class="reservoir-detail">
			<div class="reservoir-summary">
				<div class="tank-top">
					<span>{reservoir.reservoir}</span>
					<div class="capacity-reading">
						<strong>{formatNumber(reservoir.storage, 1)}<span class="unit">%</span></strong>
						<small>of capacity</small>
					</div>
				</div>
				<div class="tank">
					<span style={`width:${Math.max(0, Math.min(100, reservoir.storage ?? 0))}%`}></span>
				</div>
			</div>

			<div class="reservoir-expanded">
				<div class="metric-grid four">
					<MetricCard
						label="Storage Today"
						value={formatNumber(reservoir.storage, 1)}
						unit="%"
						icon="reservoirs"
						tone="blue"
					/>
					<MetricCard
						label="Storage Last Year"
						value={formatNumber(reservoir.previousStorage, 1)}
						unit="%"
						icon="clock"
						tone="yellow"
					/>
					<MetricCard
						label="Inflow"
						value={formatNumber(reservoir.inflow, 0)}
						unit="CUSECS"
						icon="reservoirs"
					/>
					<MetricCard
						label="Discharge"
						value={formatNumber(reservoir.discharge, 0)}
						unit="CUSECS"
						icon="reservoirs"
						tone="red"
					/>
				</div>

				<div class="reservoir-range-row">
					<span>Date range</span>
					<RangeControl bind:value={reservoirRange} options={['14D', '30D', '6M', '1Y']} />
				</div>

				<div class="chart-grid two">
					<section class="panel">
						<SectionHeader code="03A" title="Storage history" />
						<TimeSeriesChart
							data={history}
							series={[
								{
									key: 'storage',
									label: formatDate(selectedReportDate),
									color: chartColors.blue,
									fill: true
								},
								{
									key: 'previousStorage',
									label: formatDate(previousYearDate),
									color: chartColors.yellow,
									dashed: true
								}
							]}
							formatX={(value) => formatDate(String(value), true)}
							formatValue={(value) => formatNumber(value, 1)}
							yLabel="Storage (%)"
							unit="%"
							yMin={0}
							yMax={100}
						/>
					</section>
					<section class="panel">
						<SectionHeader code="03B" title="Water flow" />
						<TimeSeriesChart
							data={history}
							series={[
								{ key: 'inflow', label: 'Inflow', color: chartColors.green, fill: true },
								{ key: 'discharge', label: 'Discharge', color: chartColors.red }
							]}
							formatX={(value) => formatDate(String(value), true)}
							formatValue={(value) => formatNumber(value, 0)}
							yLabel="Flow (cusecs)"
							unit="cusecs"
						/>
					</section>
				</div>
			</div>
		</section>
	{/each}
</div>
