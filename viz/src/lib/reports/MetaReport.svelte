<script lang="ts">
	import CoverageChart from '$lib/components/CoverageChart.svelte';
	import ReportHeader from '$lib/components/ReportHeader.svelte';
	import SectionHeader from '$lib/components/SectionHeader.svelte';
	import TablePanel from '$lib/components/TablePanel.svelte';
	import type { DashboardData, ReportSnapshot } from '$lib/data/types';
	import { formatDate, formatNumber, labelSection } from './reportUtils';

	let {
		dashboard,
		reportSnapshot
	}: {
		dashboard: DashboardData;
		reportSnapshot: ReportSnapshot;
	} = $props();
</script>

<ReportHeader title="Meta" />

<section class="panel coverage-panel">
	<SectionHeader code="07A" title="Section coverage by year" />
	<div class="coverage-scroll">
		<CoverageChart
			years={dashboard.sections.years}
			sections={dashboard.sections.sections}
			{labelSection}
		/>
	</div>
</section>

<TablePanel code="07B" title="Workbook inventory">
	<table>
		<thead><tr><th>Section</th><th>Report Count</th><th>Coverage</th></tr></thead>
		<tbody>
			{#each reportSnapshot.sections.latest as row (row.section)}
				{@const total = dashboard.sections.sections.find(
					(section) => section.section === row.section
				)}
				<tr
					><td><strong>{labelSection(row.section)}</strong></td><td
						>{formatNumber(total?.reports, 0)}</td
					><td>{formatDate(total?.first ?? '', true)} → {formatDate(total?.last ?? '', true)}</td
					></tr
				>
			{/each}
		</tbody>
	</table>
</TablePanel>
