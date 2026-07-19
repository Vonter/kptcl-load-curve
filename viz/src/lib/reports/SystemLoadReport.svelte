<script lang="ts">
	import MetricCard from '$lib/components/MetricCard.svelte';
	import RangeControl from '$lib/components/RangeControl.svelte';
	import ReportHeader from '$lib/components/ReportHeader.svelte';
	import SectionHeader from '$lib/components/SectionHeader.svelte';
	import TimeSeriesChart from '$lib/components/TimeSeriesChart.svelte';
	import type { DashboardData, LoadDay, ReportSnapshot } from '$lib/data/types';
	import {
		chartColors,
		formatDate,
		formatNumericDate,
		formatHz,
		formatHour,
		formatNumber,
		sliceRange
	} from './reportUtils';

	let {
		dashboard,
		reportSnapshot,
		selectedReportDate,
		loadRange = $bindable('30D')
	}: {
		dashboard: DashboardData;
		reportSnapshot: ReportSnapshot;
		selectedReportDate: string;
		loadRange?: string;
	} = $props();

	let selectedCurve = $derived(reportSnapshot.load.curve ?? []);
	let loadYear = $derived(sliceRange(dashboard.load.daily, '1Y', selectedReportDate));
	let loadHistory = $derived(sliceRange(dashboard.load.daily, loadRange, selectedReportDate));
	let peakRow = $derived(
		loadYear.reduce(
			(best: LoadDay | null, row) =>
				!best || (row.peak ?? -Infinity) > (best.peak ?? -Infinity) ? row : best,
			null as LoadDay | null
		)
	);
	let minimumRow = $derived(
		loadYear.reduce(
			(best: LoadDay | null, row) =>
				!best || (row.minimum ?? Infinity) < (best.minimum ?? Infinity) ? row : best,
			null as LoadDay | null
		)
	);
	let annualMean = $derived(
		loadYear.length
			? loadYear.reduce((total, row) => total + (row.average ?? 0), 0) / loadYear.length
			: null
	);
	let variationRow = $derived(
		loadYear.reduce((best: (LoadDay & { variation: number }) | null, row) => {
			const variation = (row.peak ?? 0) - (row.minimum ?? 0);
			return !best || variation > best.variation ? { ...row, variation } : best;
		}, null)
	);
</script>

<ReportHeader title="System Load" />

<div class="metric-grid four">
	<MetricCard
		label="Annual peak demand"
		value={formatNumber(peakRow?.peak, 0)}
		unit="MW"
		detail={peakRow ? `${formatDate(peakRow.date)} at ${formatHour(peakRow.peakHour)}` : ''}
		icon="load"
	/>
	<MetricCard
		label="Annual minimum demand"
		value={formatNumber(minimumRow?.minimum, 0)}
		unit="MW"
		detail={minimumRow
			? `${formatDate(minimumRow.date)} at ${formatHour(minimumRow.minimumHour)}`
			: ''}
		icon="load"
		tone="blue"
	/>
	<MetricCard
		label="Annual mean demand"
		value={formatNumber(annualMean, 0)}
		unit="MW"
		detail={loadYear.length
			? `Average demand between ${formatNumericDate(loadYear[0].date)} and ${formatNumericDate(loadYear.at(-1)?.date)}`
			: ''}
		icon="summary"
		tone="yellow"
	/>
	<MetricCard
		label="Largest daily variation"
		value={formatNumber(variationRow?.variation, 0)}
		unit="MW"
		detail={variationRow ? formatDate(variationRow.date) : ''}
		icon="load"
		tone="red"
	/>
</div>

<section class="panel full-panel first-panel">
	<SectionHeader code="01A" title="Annual overview" />
	<div class="chart-grid two">
		<TimeSeriesChart
			data={loadYear}
			height={245}
			series={[
				{ key: 'peak', label: 'Peak demand', color: chartColors.green },
				{ key: 'minimum', label: 'Minimum demand', color: chartColors.blue }
			]}
			band={{ lowerKey: 'minimum', upperKey: 'peak', color: chartColors.green }}
			formatX={(value) => formatDate(String(value), true)}
			formatValue={(value) => formatNumber(value, 0)}
			yLabel="Demand (MW)"
			unit="MW"
		/>
		<TimeSeriesChart
			data={loadYear}
			height={245}
			series={[
				{ key: 'minHz', label: 'Frequency low', color: chartColors.red },
				{ key: 'maxHz', label: 'Frequency high', color: chartColors.yellow }
			]}
			formatX={(value) => formatDate(String(value), true)}
			formatValue={formatHz}
			yLabel="Frequency (Hz)"
			unit="Hz"
		/>
	</div>
</section>

<div class="panel-grid equal">
	<section class="panel">
		<SectionHeader code="01B" title="Hourly load profile" />
		<TimeSeriesChart
			data={selectedCurve}
			xKey="hour"
			series={[{ key: 'load', label: 'Grid load', color: chartColors.green, fill: true }]}
			formatX={formatHour}
			formatValue={(value) => formatNumber(value, 0)}
			xTicks={[0, 6, 12, 18, 24]}
			yLabel="Demand (MW)"
			unit="MW"
		/>
	</section>
	<section class="panel">
		<SectionHeader code="01C" title="Daily demand envelope">
			{#snippet actions()}
				<RangeControl bind:value={loadRange} options={['7D', '14D', '30D', '1Y']} />
			{/snippet}
		</SectionHeader>
		<TimeSeriesChart
			data={loadHistory}
			series={[
				{ key: 'peak', label: 'Peak', color: chartColors.green },
				{ key: 'average', label: 'Average', color: chartColors.yellow, dashed: true },
				{ key: 'minimum', label: 'Minimum', color: chartColors.blue }
			]}
			band={{ lowerKey: 'minimum', upperKey: 'peak', color: chartColors.green }}
			formatX={(value) => formatDate(String(value), true)}
			formatValue={(value) => formatNumber(value, 0)}
			yLabel="Demand (MW)"
			unit="MW"
		/>
	</section>
</div>

<div class="panel-grid equal">
	<section class="panel">
		<SectionHeader code="01D" title="Hourly frequency trace" />
		<TimeSeriesChart
			data={selectedCurve}
			xKey="hour"
			series={[{ key: 'frequency', label: 'Frequency', color: chartColors.red }]}
			formatX={formatHour}
			formatValue={formatHz}
			xTicks={[0, 6, 12, 18, 24]}
			yLabel="Frequency (Hz)"
			unit="Hz"
			yMin={49.75}
			yMax={50.25}
			target={{ min: 49.9, max: 50.1, color: chartColors.green }}
		/>
	</section>
	<section class="panel">
		<SectionHeader code="01E" title="Daily frequency envelope">
			{#snippet actions()}
				<RangeControl bind:value={loadRange} options={['7D', '14D', '30D', '1Y']} />
			{/snippet}
		</SectionHeader>
		<TimeSeriesChart
			data={loadHistory}
			series={[
				{ key: 'maxHz', label: 'Maximum', color: chartColors.green },
				{ key: 'averageHz', label: 'Average', color: chartColors.blue, dashed: true },
				{ key: 'minHz', label: 'Minimum', color: chartColors.red }
			]}
			band={{ lowerKey: 'minHz', upperKey: 'maxHz', color: chartColors.blue }}
			formatX={(value) => formatDate(String(value), true)}
			formatValue={formatHz}
			yLabel="Frequency (Hz)"
			unit="Hz"
			target={{ min: 49.9, max: 50.1, color: chartColors.green }}
		/>
	</section>
</div>
