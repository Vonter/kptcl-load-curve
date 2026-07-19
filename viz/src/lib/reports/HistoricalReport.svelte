<script lang="ts">
	import { untrack } from 'svelte';
	import ReportHeader from '$lib/components/ReportHeader.svelte';
	import SectionHeader from '$lib/components/SectionHeader.svelte';
	import TimeSeriesChart from '$lib/components/TimeSeriesChart.svelte';
	import type { ChartDatum, HistoricalData } from '$lib/data/types';
	import { chartColors, formatDate, formatHz, formatNumber, seriesFor } from './reportUtils';

	let { historical }: { historical: HistoricalData } = $props();

	const initialCoverage = untrack(() => historical.coverage);
	const firstYear = Number(initialCoverage[0].slice(0, 4));
	const lastYear = Number(initialCoverage[1].slice(0, 4));
	const years = Array.from({ length: lastYear - firstYear + 1 }, (_, index) => firstYear + index);

	let fromYear = $state(firstYear);
	let toYear = $state(lastYear);

	function selectFromYear(year: number) {
		fromYear = year;
		if (toYear < year) toYear = year;
	}

	function selectToYear(year: number) {
		toYear = year;
		if (fromYear > year) fromYear = year;
	}

	function selectAllYears() {
		fromYear = firstYear;
		toYear = lastYear;
	}

	function inSelectedYears(row: ChartDatum): boolean {
		const year = Number(String(row.date).slice(0, 4));
		return year >= fromYear && year <= toYear;
	}

	let filteredLoad = $derived(historical.load.filter(inSelectedYears));
	let filteredGeneration = $derived(historical.generation.filter(inSelectedYears));
	let filteredGenerationSources = $derived(
		historical.generationSources.history.filter(inSelectedYears)
	);
	let filteredReservoirs = $derived(historical.reservoirs.history.filter(inSelectedYears));
	let filteredOutages = $derived(historical.outages.filter(inSelectedYears));
	let selectedRangeLabel = $derived(
		fromYear === toYear ? String(fromYear) : `${fromYear} – ${toYear}`
	);
	let isFullRange = $derived(fromYear === firstYear && toYear === lastYear);
</script>

<ReportHeader title="Historical">
	{#snippet actions()}
		<div class="year-range">
			<div class="range-heading">
				<button type="button" onclick={selectAllYears} disabled={isFullRange}>All years</button>
			</div>
			<div class="range-fields" role="group" aria-labelledby="historical-year-range-label">
				<label>
					<span>From</span>
					<select
						aria-label="From year"
						value={fromYear}
						onchange={(event) => selectFromYear(Number(event.currentTarget.value))}
					>
						{#each years as year (year)}
							<option value={year}>{year}</option>
						{/each}
					</select>
				</label>
				<span class="range-separator" aria-hidden="true">to</span>
				<label>
					<span>To</span>
					<select
						aria-label="To year"
						value={toYear}
						onchange={(event) => selectToYear(Number(event.currentTarget.value))}
					>
						{#each years as year (year)}
							<option value={year}>{year}</option>
						{/each}
					</select>
				</label>
			</div>
		</div>
	{/snippet}
</ReportHeader>

<section class="panel full-panel">
	<SectionHeader code="06A" title="System demand history" detail={selectedRangeLabel} />
	<TimeSeriesChart
		data={filteredLoad}
		series={[
			{ key: 'peak', label: 'Monthly peak', color: chartColors.green },
			{ key: 'average', label: 'Monthly average', color: chartColors.yellow, dashed: true },
			{ key: 'minimum', label: 'Monthly minimum', color: chartColors.blue }
		]}
		band={{ lowerKey: 'minimum', upperKey: 'peak', color: chartColors.green }}
		formatX={(value) => formatDate(String(value), true)}
		formatValue={(value) => formatNumber(value, 0)}
		yLabel="Demand (MW)"
		unit="MW"
	/>
</section>

<div class="panel-grid equal">
	<section class="panel">
		<SectionHeader code="06B" title="Grid frequency history" />
		<TimeSeriesChart
			data={filteredLoad}
			series={[
				{ key: 'maxHz', label: 'Monthly maximum', color: chartColors.green },
				{ key: 'averageHz', label: 'Monthly average', color: chartColors.blue, dashed: true },
				{ key: 'minHz', label: 'Monthly minimum', color: chartColors.red }
			]}
			band={{ lowerKey: 'minHz', upperKey: 'maxHz', color: chartColors.blue }}
			formatX={(value) => formatDate(String(value), true)}
			formatValue={formatHz}
			yLabel="Frequency (Hz)"
			unit="Hz"
		/>
	</section>
	<section class="panel">
		<SectionHeader code="06C" title="Daily energy supplied" />
		<TimeSeriesChart
			data={filteredGeneration}
			series={[{ key: 'energy', label: 'Energy supplied', color: chartColors.yellow, fill: true }]}
			formatX={(value) => formatDate(String(value), true)}
			formatValue={(value) => formatNumber(value, 1)}
			yLabel="Monthly energy (MU)"
			unit="MU"
		/>
	</section>
</div>

<div class="panel-grid equal">
	<section class="panel">
		<SectionHeader code="06D" title="Installed generation capacity" />
		<TimeSeriesChart
			data={filteredGeneration}
			series={[{ key: 'capacity', label: 'Installed capacity', color: chartColors.green }]}
			formatX={(value) => formatDate(String(value), true)}
			formatValue={(value) => formatNumber(value, 0)}
			yLabel="Capacity (MW)"
			unit="MW"
		/>
	</section>
	<section class="panel">
		<SectionHeader code="06E" title="Generation by source" />
		<TimeSeriesChart
			data={filteredGenerationSources}
			series={seriesFor(historical.generationSources.names)}
			formatX={(value) => formatDate(String(value), true)}
			formatValue={(value) => formatNumber(value, 1)}
			yLabel="Monthly energy (MU)"
			unit="MU"
		/>
	</section>
</div>

<section class="panel full-panel">
	<SectionHeader code="06F" title="Reservoir storage history" />
	<TimeSeriesChart
		data={filteredReservoirs}
		series={seriesFor(historical.reservoirs.names)}
		formatX={(value) => formatDate(String(value), true)}
		formatValue={(value) => formatNumber(value, 1)}
		yLabel="Monthly storage (%)"
		unit="%"
		yMin={0}
		yMax={100}
	/>
</section>

<section class="panel full-panel">
	<SectionHeader code="06G" title="Reported outages history" />
	<TimeSeriesChart
		data={filteredOutages}
		series={[
			{ key: 'total', label: 'All outages', color: chartColors.ink },
			{ key: 'forced', label: 'Forced units', color: chartColors.red },
			{ key: 'planned', label: 'Planned units', color: chartColors.yellow },
			{ key: 'lines', label: 'Major lines', color: chartColors.blue }
		]}
		formatX={(value) => formatDate(String(value), true)}
		formatValue={(value) => formatNumber(value, 0)}
		yLabel="Monthly outages"
	/>
</section>

<style>
	.year-range {
		width: 224px;
	}

	.range-heading {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 16px;
		margin-bottom: 7px;
	}

	.range-heading button {
		border: 0;
		background: transparent;
		padding: 1px 0;
		font-family: var(--font-mono);
		font-size: 0.56rem;
		font-weight: 700;
		color: var(--green);
		cursor: pointer;
	}

	.range-heading button:hover:not(:disabled) {
		text-decoration: underline;
		text-underline-offset: 3px;
	}

	.range-heading button:disabled {
		opacity: 0;
		cursor: default;
	}

	.range-fields {
		display: grid;
		grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
		align-items: end;
		gap: 10px;
	}

	label {
		display: grid;
		gap: 3px;
		border-bottom: 1px solid var(--line-strong);
		padding-bottom: 5px;
		transition: border-color 120ms ease;
	}

	label:focus-within {
		border-color: var(--ink);
	}

	label span {
		font-family: var(--font-mono);
		font-size: 0.5rem;
		font-weight: 700;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--muted);
	}

	select {
		width: 100%;
		border: 0;
		border-radius: 0;
		outline: 0;
		background: transparent;
		padding: 0;
		font-family: var(--font-mono);
		font-size: 0.78rem;
		font-weight: 750;
		color: var(--ink);
		cursor: pointer;
	}

	.range-separator {
		padding-bottom: 7px;
		font-family: var(--font-mono);
		font-size: 0.56rem;
		color: var(--muted);
	}

	@media (max-width: 620px) {
		.year-range {
			width: min(100%, 250px);
		}
	}
</style>
