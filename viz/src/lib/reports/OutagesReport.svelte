<script lang="ts">
	import Icon from '$lib/components/Icon.svelte';
	import MetricCard from '$lib/components/MetricCard.svelte';
	import RangeControl from '$lib/components/RangeControl.svelte';
	import ReportHeader from '$lib/components/ReportHeader.svelte';
	import SectionHeader from '$lib/components/SectionHeader.svelte';
	import TablePanel from '$lib/components/TablePanel.svelte';
	import TimeSeriesChart from '$lib/components/TimeSeriesChart.svelte';
	import type { DashboardData, ReportSnapshot } from '$lib/data/types';
	import { chartColors, formatDate, formatNumber, sliceRange, systemLabel } from './reportUtils';

	let {
		dashboard,
		reportSnapshot,
		selectedReportDate,
		outageRange = $bindable('30D'),
		outageFilter = $bindable('all'),
		outageSearch = $bindable('')
	}: {
		dashboard: DashboardData;
		reportSnapshot: ReportSnapshot;
		selectedReportDate: string;
		outageRange?: string;
		outageFilter?: string;
		outageSearch?: string;
	} = $props();

	let outageHistory = $derived(
		sliceRange(dashboard.outages.history, outageRange, selectedReportDate)
	);
	let outageLatest = $derived(
		dashboard.outages.history.find((row) => row.date === selectedReportDate)
	);
	let filteredEvents = $derived(
		reportSnapshot.outages.events.filter((event) => {
			const matchesFilter =
				outageFilter === 'all' || event.type === outageFilter || event.system === outageFilter;
			const search = outageSearch.trim().toLowerCase();
			return (
				matchesFilter &&
				(!search ||
					[event.asset, event.details, event.remarks]
						.filter(Boolean)
						.some((value) => String(value).toLowerCase().includes(search)))
			);
		})
	);
</script>

<ReportHeader title="Outages" />

<div class="metric-grid four">
	<MetricCard
		label="Total reported outages"
		value={formatNumber(outageLatest?.total, 0)}
		icon="outages"
		tone="red"
	/>
	<MetricCard
		label="Forced units"
		value={formatNumber(outageLatest?.forced, 0)}
		icon="outages"
		tone="red"
	/>
	<MetricCard
		label="Planned units"
		value={formatNumber(outageLatest?.planned, 0)}
		icon="calendar"
		tone="yellow"
	/>
	<MetricCard
		label="Major lines"
		value={formatNumber(outageLatest?.lines, 0)}
		icon="breaker"
		tone="blue"
	/>
</div>

<section class="panel full-panel">
	<SectionHeader code="04A" title="Daily outages">
		{#snippet actions()}<RangeControl bind:value={outageRange} />{/snippet}
	</SectionHeader>
	<TimeSeriesChart
		data={outageHistory}
		series={[
			{ key: 'lines', label: 'Major lines', color: chartColors.blue },
			{ key: 'forced', label: 'Forced units', color: chartColors.red },
			{ key: 'planned', label: 'Planned units', color: chartColors.yellow }
		]}
		formatX={(value) => formatDate(String(value), true)}
		formatValue={(value) => formatNumber(value, 0)}
		yLabel="Outages"
	/>
</section>

<TablePanel code="04B" title="Outage list" alignActions="center">
	{#snippet actions()}
		<div class="event-controls">
			<div class="selector-bank small">
				{#each [['all', 'All'], ['forced', 'Forced'], ['planned', 'Planned'], ['major_line', 'Lines']] as filter (filter[0])}
					<button
						class:active={outageFilter === filter[0]}
						type="button"
						onclick={() => (outageFilter = filter[0])}>{filter[1]}</button
					>
				{/each}
			</div>
			<label class="search-box"
				><Icon name="search" size={15} /><input
					bind:value={outageSearch}
					placeholder="Find asset"
					aria-label="Find outage asset"
				/></label
			>
		</div>
	{/snippet}
	<table>
		<thead
			><tr
				><th>System / class</th><th>Asset</th><th>Condition / detail</th><th>From</th><th>To</th><th
					>Remarks</th
				></tr
			></thead
		>
		<tbody>
			{#each filteredEvents as event, index (index)}
				<tr>
					<td
						><span class={`status-tag ${event.type}`}>{systemLabel(event.type)}</span><small
							>{systemLabel(event.system)}</small
						></td
					>
					<td><strong>{event.asset}</strong></td>
					<td class="detail-cell">{event.details ?? '—'}</td>
					<td>{event.from ?? '—'}</td><td>{event.to ?? '—'}</td><td>{event.remarks ?? '—'}</td>
				</tr>
			{/each}
			{#if !filteredEvents.length}<tr
					><td colspan="6" class="empty-table">No events match this filter.</td></tr
				>{/if}
		</tbody>
	</table>
</TablePanel>
