<script lang="ts">
	import BarChart from '$lib/components/BarChart.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import MetricCard from '$lib/components/MetricCard.svelte';
	import ReportHeader from '$lib/components/ReportHeader.svelte';
	import SectionHeader from '$lib/components/SectionHeader.svelte';
	import TablePanel from '$lib/components/TablePanel.svelte';
	import TimeSeriesChart from '$lib/components/TimeSeriesChart.svelte';
	import type { DashboardData, ReportSnapshot } from '$lib/data/types';
	import { chartColors, formatDate, formatHour, formatNumber } from './reportUtils';

	let {
		dashboard,
		reportSnapshot,
		selectedReportDate
	}: {
		dashboard: DashboardData;
		reportSnapshot: ReportSnapshot;
		selectedReportDate: string;
	} = $props();

	let effectiveDate = $derived(
		reportSnapshot.summary.available ? selectedReportDate : dashboard.summary.reportDate
	);
	let summaryLatest = $derived(dashboard.summary.grid.find((row) => row.date === effectiveDate));
	let summaryCurve = $derived(
		reportSnapshot.summary.available ? reportSnapshot.load.curve : dashboard.summary.curve
	);
	let summaryGeneration = $derived(
		(reportSnapshot.summary.available
			? reportSnapshot.summary.generation
			: dashboard.summary.generation
		).slice(0, 14)
	);
	let summaryExchange = $derived(
		reportSnapshot.summary.available ? reportSnapshot.summary.exchange : dashboard.summary.exchange
	);
	let summaryOutages = $derived(
		dashboard.outages.history.find((row) => row.date === effectiveDate)
	);
</script>

<ReportHeader title="Daily" />

{#if effectiveDate !== selectedReportDate}
	<div class="source-note">
		<Icon name="clock" size={16} />
		<span
			>Daily data is not available for {formatDate(selectedReportDate)}. Showing the most recent
			available report from {formatDate(effectiveDate)}.</span
		>
	</div>
{/if}

<div class="metric-grid four">
	<MetricCard
		label="Maximum demand"
		value={formatNumber(summaryLatest?.maximumDemand, 0)}
		unit="MW"
		icon="load"
		tone="yellow"
	/>
	<MetricCard
		label="Minimum demand"
		value={formatNumber(summaryLatest?.minimumDemand, 0)}
		unit="MW"
		icon="load"
		tone="blue"
	/>
	<MetricCard
		label="Energy consumed"
		value={formatNumber(summaryLatest?.energy, 2)}
		unit="MU"
		icon="summary"
	/>
	<MetricCard
		label="Total outages"
		value={formatNumber(summaryOutages?.total, 0)}
		unit="EVENTS"
		icon="outages"
		tone="red"
	/>
</div>

<section class="panel full-panel">
	<SectionHeader code="05A" title={`Hourly demand · ${formatDate(effectiveDate)}`} />
	<TimeSeriesChart
		data={summaryCurve}
		xKey="hour"
		series={[{ key: 'load', label: 'Grid load', color: chartColors.green, fill: true }]}
		formatX={formatHour}
		formatValue={(value) => formatNumber(value, 0)}
		xTicks={[0, 6, 12, 18, 24]}
		yLabel="Demand (MW)"
		unit="MW"
	/>
</section>

<div class="panel-grid equal">
	<section class="panel">
		<SectionHeader code="05B" title={`Hourly frequency · ${formatDate(effectiveDate)}`} />
		<TimeSeriesChart
			data={summaryCurve}
			xKey="hour"
			series={[{ key: 'frequency', label: 'Frequency', color: chartColors.red }]}
			formatX={formatHour}
			formatValue={(value) => formatNumber(value, 2)}
			xTicks={[0, 6, 12, 18, 24]}
			yLabel="Frequency (Hz)"
			unit="Hz"
		/>
	</section>
	<section class="panel">
		<SectionHeader code="05C" title={`Generation contributors  · ${formatDate(effectiveDate)}`} />
		<BarChart
			data={summaryGeneration}
			labelKey="entity"
			valueKey="value"
			color={chartColors.green}
			xLabel="Energy (MU)"
			unit="MU"
		/>
	</section>
</div>

<TablePanel code="05D" title={`Exchange register · ${formatDate(effectiveDate)}`}>
	<table>
		<thead><tr><th>Entity</th><th>Value</th></tr></thead>
		<tbody>
			{#each summaryExchange as row (`${row.entity}-${row.metric}`)}
				<tr
					><td><strong>{row.entity}</strong></td><td
						>{formatNumber(row.value, 3)}
						{#if row.unit}<span class="unit"> {row.unit}</span>{/if}</td
					></tr
				>
			{/each}
		</tbody>
	</table>
</TablePanel>
