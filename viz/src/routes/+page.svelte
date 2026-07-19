<script lang="ts">
	import { onMount } from 'svelte';
	import DashboardHeader from '$lib/components/DashboardHeader.svelte';
	import LoadState from '$lib/components/LoadState.svelte';
	import SEO from '$lib/components/SEO.svelte';
	import {
		loadDashboard as fetchDashboard,
		loadHistorical as fetchHistorical,
		loadReportYears,
		nearestDate
	} from '$lib/data/loaders';
	import type { DashboardData, DateReports, HistoricalData } from '$lib/data/types';
	import DailySummaryReport from '$lib/reports/DailySummaryReport.svelte';
	import GenerationReport from '$lib/reports/GenerationReport.svelte';
	import HistoricalReport from '$lib/reports/HistoricalReport.svelte';
	import MetaReport from '$lib/reports/MetaReport.svelte';
	import OutagesReport from '$lib/reports/OutagesReport.svelte';
	import ReservoirsReport from '$lib/reports/ReservoirsReport.svelte';
	import SystemLoadReport from '$lib/reports/SystemLoadReport.svelte';
	import { isReportId, reports, type ReportId } from '$lib/reports/config';

	let dashboard = $state<DashboardData | null>(null);
	let historical = $state<HistoricalData | null>(null);
	let dateReports = $state<DateReports>({});
	let activeReport = $state<ReportId>('load');
	let selectedReportDate = $state('');
	let loadingError = $state('');
	let historicalError = $state('');
	let dashboardLoading = $state(false);
	let historicalLoading = $state(false);
	let snapshotLoading = $state(false);
	let reportSwitcher = $state<HTMLElement>();
	let snapshotRequest = 0;

	let loadRange = $state('30D');
	let stationRange = $state('1Y');
	let reservoirRange = $state('1Y');
	let outageRange = $state('30D');
	let outageFilter = $state('all');
	let outageSearch = $state('');

	function reportFromUrl(): ReportId {
		const value = new URLSearchParams(window.location.search).get('report');
		return isReportId(value) ? value : 'load';
	}

	function chooseReport(id: ReportId, event?: MouseEvent) {
		event?.preventDefault();
		activeReport = id;
		const url = new URL(window.location.href);
		url.searchParams.set('report', id);
		window.history.pushState({ report: id }, '', url);
		if (id === 'historical') void ensureHistorical();
		else void ensureDashboard();
		centerReportTab(id);
		window.scrollTo({ top: 0, behavior: 'smooth' });
	}

	function centerReportTab(id: ReportId, behavior: ScrollBehavior = 'smooth') {
		if (!reportSwitcher || !window.matchMedia('(max-width: 880px)').matches) return;
		requestAnimationFrame(() => {
			const tab = reportSwitcher?.querySelector<HTMLElement>(`[data-report="${id}"]`);
			if (!tab || !reportSwitcher) return;
			reportSwitcher.scrollTo({
				left: tab.offsetLeft - (reportSwitcher.clientWidth - tab.offsetWidth) / 2,
				behavior
			});
		});
	}

	async function ensureHistorical() {
		if (historical || historicalLoading) return;
		historicalLoading = true;
		historicalError = '';
		try {
			historical = await fetchHistorical();
		} catch (error) {
			historicalError = error instanceof Error ? error.message : 'Could not load historical data';
		} finally {
			historicalLoading = false;
		}
	}

	async function ensureDashboard() {
		if (dashboard || dashboardLoading) return;
		dashboardLoading = true;
		loadingError = '';
		try {
			dashboard = await fetchDashboard();
			const requested = new URLSearchParams(window.location.search).get('date');
			await selectDate(requested ?? dashboard.reportDates.at(-1) ?? '');
		} catch (error) {
			loadingError = error instanceof Error ? error.message : 'Could not load data';
		} finally {
			dashboardLoading = false;
		}
	}

	async function selectDate(value: string, updateUrl = true) {
		if (!dashboard?.reportDates.length) return;
		const date = nearestDate(value, dashboard.reportDates);
		selectedReportDate = date;
		if (updateUrl) {
			const url = new URL(window.location.href);
			url.searchParams.set('date', date);
			window.history.replaceState({ report: activeReport, date }, '', url);
		}

		const request = ++snapshotRequest;
		snapshotLoading = true;
		loadingError = '';
		try {
			const loadedReports = await loadReportYears(date, dashboard.reportDates[0]);
			if (request === snapshotRequest) dateReports = loadedReports;
		} catch (error) {
			if (request === snapshotRequest) {
				loadingError = error instanceof Error ? error.message : 'Could not load report data';
			}
		} finally {
			if (request === snapshotRequest) snapshotLoading = false;
		}
	}

	onMount(() => {
		activeReport = reportFromUrl();
		centerReportTab(activeReport, 'auto');
		const handleHistory = () => {
			activeReport = reportFromUrl();
			centerReportTab(activeReport);
			if (activeReport === 'historical') void ensureHistorical();
			else if (dashboard) {
				const requested = new URLSearchParams(window.location.search).get('date');
				void selectDate(requested ?? dashboard.reportDates.at(-1) ?? '', false);
			} else void ensureDashboard();
		};
		window.addEventListener('popstate', handleHistory);
		if (activeReport === 'historical') void ensureHistorical();
		else void ensureDashboard();
		return () => window.removeEventListener('popstate', handleHistory);
	});

	let currentReport = $derived(reports.find((report) => report.id === activeReport) ?? reports[0]);
	let reportDescription = $derived(
		`${currentReport.label} interactive charts and data from KPTCL Load Curve reports.`
	);
	let reportSnapshot = $derived(dateReports[selectedReportDate] ?? null);
	let displayDate = $derived(
		activeReport === 'summary' && reportSnapshot?.summary.available === false
			? (dashboard?.summary.reportDate ?? '')
			: selectedReportDate
	);
</script>

<SEO title={currentReport.label} description={reportDescription} />

<div class="app-shell">
	<DashboardHeader
		{activeReport}
		selectedDate={selectedReportDate}
		{displayDate}
		minDate={dashboard?.reportDates[0] ?? ''}
		maxDate={dashboard?.reportDates.at(-1) ?? ''}
		disabled={!dashboard || snapshotLoading}
		bind:switcher={reportSwitcher}
		onChoose={chooseReport}
		onDate={(date) => void selectDate(date)}
	/>

	{#if activeReport === 'historical' || (dashboard && reportSnapshot)}
		<main>
			<div class="report-content">
				{#if activeReport === 'historical'}
					{#if historical}
						<HistoricalReport {historical} />
					{:else if historicalError}
						<LoadState inline error={historicalError} title="Historical data unavailable" />
					{:else}
						<LoadState inline />
					{/if}
				{:else if dashboard && reportSnapshot}
					{#if activeReport === 'load'}
						<SystemLoadReport {dashboard} {reportSnapshot} {selectedReportDate} bind:loadRange />
					{:else if activeReport === 'stations'}
						<GenerationReport
							{dashboard}
							{reportSnapshot}
							{selectedReportDate}
							{dateReports}
							bind:stationRange
						/>
					{:else if activeReport === 'reservoirs'}
						<ReservoirsReport {dashboard} {selectedReportDate} bind:reservoirRange />
					{:else if activeReport === 'outages'}
						<OutagesReport
							{dashboard}
							{reportSnapshot}
							{selectedReportDate}
							bind:outageRange
							bind:outageFilter
							bind:outageSearch
						/>
					{:else if activeReport === 'summary'}
						<DailySummaryReport {dashboard} {reportSnapshot} {selectedReportDate} />
					{:else}
						<MetaReport {dashboard} {reportSnapshot} />
					{/if}
				{/if}
			</div>
		</main>
	{:else if loadingError}
		<LoadState error={loadingError} />
	{:else}
		<LoadState />
	{/if}
</div>

<style>
	.app-shell {
		min-height: 100vh;
	}
	main {
		width: min(1480px, calc(100% - 40px));
		margin: 0 auto;
		padding: 34px 0 64px;
	}
	@media (max-width: 880px) {
		main {
			width: min(100% - 24px, 1480px);
			padding-top: 26px;
		}
	}
	@media (max-width: 620px) {
		main {
			width: min(100% - 16px, 1480px);
			padding-top: 22px;
		}
	}
</style>
