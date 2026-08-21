<script lang="ts">
	import { onMount, tick } from 'svelte';
	import DashboardHeader from '$lib/components/DashboardHeader.svelte';
	import LoadState from '$lib/components/LoadState.svelte';
	import SEO from '$lib/components/SEO.svelte';
	import WorkbookFields from '$lib/components/WorkbookFields.svelte';
	import WorkbookSheet from '$lib/components/WorkbookSheet.svelte';
	import { loadWorkbook } from '$lib/data/loaders';
	import type { WorkbookCell, WorkbookData } from '$lib/data/types';
	import {
		buildOriginIndex,
		displayValue,
		recordAddresses,
		type Selection
	} from '$lib/data/workbook';
	import { labelSection } from '$lib/reports/reportUtils';

	const ZOOM_MIN = 0.1;
	const ZOOM_MAX = 2;
	const ZOOM_STEP = 1.25;
	const ZOOM_DEFAULT = 0.6;

	let data = $state<WorkbookData | null>(null);
	let loadingError = $state('');
	let activeId = $state('');
	let selection = $state<Selection | null>(null);
	let fieldsPane = $state<HTMLElement>();
	let sheetPane = $state<HTMLElement>();
	let zoom = $state(ZOOM_DEFAULT);
	let fitted = $state(false);

	let originIndex = $derived(buildOriginIndex(data?.datasets ?? []));
	let mapped = $derived(new Set(originIndex.keys()));
	let cellByAddress = $derived(
		new Map((data?.cells ?? []).map((cell): [string, WorkbookCell] => [cell.a, cell]))
	);
	let dataset = $derived(data?.datasets.find((entry) => entry.id === activeId) ?? null);
	let record = $derived(
		selection && dataset?.id === selection.datasetId
			? (dataset.records[selection.recordIndex] ?? null)
			: null
	);
	let hitAddresses = $derived(
		selection && record ? (record.cells[selection.field] ?? []) : ([] as string[])
	);
	let hit = $derived(new Set(hitAddresses));
	let kin = $derived.by(() => {
		if (!dataset || !selection || dataset.id !== selection.datasetId) return new Set<string>();
		const addresses = recordAddresses(dataset, selection.recordIndex);
		return new Set(addresses.filter((address) => !hit.has(address)));
	});
	let anchorCell = $derived(cellByAddress.get(hitAddresses[0] ?? '') ?? null);

	/** Scroll a pane to its target without dragging the whole page along. */
	function reveal(pane: HTMLElement | undefined, selector: string) {
		const target = pane?.querySelector<HTMLElement>(selector);
		if (!pane || !target) return;
		const frame = pane.getBoundingClientRect();
		const spot = target.getBoundingClientRect();
		if (spot.top < frame.top + 34 || spot.bottom > frame.bottom - 8) {
			pane.scrollTop += spot.top - frame.top - frame.height / 2 + spot.height / 2;
		}
		if (spot.left < frame.left + 52 || spot.right > frame.right - 8) {
			pane.scrollLeft += spot.left - frame.left - frame.width / 2 + spot.width / 2;
		}
	}

	/** The largest zoom that still leaves the whole sheet inside the pane. */
	function wholeSheetZoom(): number {
		const sheet = sheetPane?.querySelector('table');
		if (!sheetPane || !sheet) return 1;
		const box = sheet.getBoundingClientRect();
		const width = box.width / zoom;
		const height = box.height / zoom;
		if (!width || !height) return 1;
		const scale = Math.min(sheetPane.clientWidth / width, sheetPane.clientHeight / height);
		return Math.max(ZOOM_MIN, Math.min(1, Math.floor(scale * 100) / 100));
	}

	function fitSheet() {
		zoom = wholeSheetZoom();
		fitted = true;
	}

	function scaleSheet(factor: number) {
		zoom = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, Math.round(zoom * factor * 100) / 100));
		fitted = false;
	}

	async function pickField(recordIndex: number, field: string) {
		const [address] = dataset?.records[recordIndex]?.cells[field] ?? [];
		selection = { datasetId: activeId, recordIndex, field };
		await tick();
		if (address) reveal(sheetPane, `[data-address="${address}"]`);
	}

	async function pickCell(address: string) {
		const [origin] = originIndex.get(address) ?? [];
		if (!origin) return;
		activeId = origin.datasetId;
		selection = { ...origin };
		await tick();
		reveal(fieldsPane, `[data-key="${origin.recordIndex}:${origin.field}"]`);
	}

	function chooseDataset(id: string) {
		activeId = id;
		selection = null;
		if (fieldsPane) fieldsPane.scrollTo({ top: 0, left: 0 });
	}

	onMount(() => {
		const refit = () => {
			if (fitted) fitSheet();
		};
		window.addEventListener('resize', refit);

		void (async () => {
			try {
				const loaded = await loadWorkbook();
				data = loaded;
				const first = loaded.datasets[0];
				if (!first) return;
				activeId = first.id;
				const index = first.records.findIndex((entry) => Object.keys(entry.cells).length > 0);
				const target = first.records[index];
				if (!target) return;
				selection = {
					datasetId: first.id,
					recordIndex: index,
					field: Object.keys(target.cells)[0]
				};
			} catch (error) {
				loadingError = error instanceof Error ? error.message : 'Could not load workbook data';
			}
		})();

		return () => window.removeEventListener('resize', refit);
	});
</script>

<SEO
	title="Workbook"
	description="Trace every value in the KPTCL dataset back to the exact cell of the published Excel report it was read from."
/>

<div class="workbook-shell">
	<DashboardHeader activeReport="workbook" />

	{#if data && dataset}
		<div class="trace-bar">
			<p class="trace-file">
				<span>File</span>
				<a href={data.sourceUrl} target="_blank" rel="external noreferrer" title={data.workbook}>
					{data.workbook}
				</a>
			</p>
			<div class="trace-flow">
				{#if selection && record}
					{#each hitAddresses as address (address)}
						<b class="trace-cell">{address}</b>
					{/each}
					{#if anchorCell?.s}
						<span class="trace-section">{labelSection(anchorCell.s)}</span>
					{/if}
					<span class="trace-arrow" aria-hidden="true">→</span>
					<span class="trace-path">
						{dataset.label}<i>/</i>{record.label}<i>/</i><em>{selection.field}</em>
					</span>
					<span class="trace-value">{displayValue(record.values[selection.field]) || '—'}</span>
				{:else}
					<span class="trace-hint"
						>Select a highlighted value to trace it to its workbook cell.</span
					>
				{/if}
			</div>
		</div>

		<div class="split">
			<section class="pane">
				<div class="pane-head">
					<h2>Source workbook</h2>
					<div class="pane-tools">
						<div class="zoom">
							<button
								type="button"
								onclick={() => scaleSheet(1 / ZOOM_STEP)}
								disabled={zoom <= ZOOM_MIN}
								aria-label="Zoom out">−</button
							>
							<output>{Math.round(zoom * 100)}%</output>
							<button
								type="button"
								onclick={() => scaleSheet(ZOOM_STEP)}
								disabled={zoom >= ZOOM_MAX}
								aria-label="Zoom in">+</button
							>
							<button type="button" class="fit" class:active={fitted} onclick={fitSheet}>Fit</button
							>
						</div>
					</div>
				</div>
				<div class="pane-body sheet" bind:this={sheetPane}>
					<div class="sheet-zoom" style="zoom: {zoom}">
						<WorkbookSheet
							cells={data.cells}
							rows={data.sheet.rows}
							columns={data.sheet.columns}
							{mapped}
							{kin}
							{hit}
							onPick={pickCell}
						/>
					</div>
				</div>
			</section>

			<section class="pane">
				<div class="pane-head">
					<h2>Extracted dataset</h2>
					<nav class="dataset-tabs" aria-label="Dataset">
						{#each data.datasets as entry (entry.id)}
							<button
								type="button"
								class:active={entry.id === activeId}
								aria-current={entry.id === activeId ? 'true' : undefined}
								onclick={() => chooseDataset(entry.id)}
							>
								{entry.label}
							</button>
						{/each}
					</nav>
				</div>
				<div class="pane-body" bind:this={fieldsPane}>
					<WorkbookFields {dataset} {selection} onPick={pickField} />
				</div>
			</section>
		</div>
	{:else if loadingError}
		<LoadState error={loadingError} title="Workbook data unavailable" />
	{:else}
		<LoadState />
	{/if}
</div>

<style>
	.workbook-shell {
		display: flex;
		flex-direction: column;
		height: 100vh;
		min-width: 0;
	}

	.workbook-shell > :global(header) {
		flex: 0 0 auto;
	}

	.trace-bar {
		display: flex;
		flex: 0 0 auto;
		align-items: stretch;
		min-height: 38px;
		overflow: hidden;
		border-bottom: 1px solid var(--line);
		background: var(--paper);
		font-family: var(--font-mono);
		font-size: 0.63rem;
	}

	.trace-file {
		display: flex;
		flex: 0 0 auto;
		align-items: center;
		gap: 9px;
		max-width: 40%;
		margin: 0;
		border-right: 1px solid var(--line);
		background: var(--paper-deep);
		padding: 0 16px;
	}

	.trace-file span {
		flex: 0 0 auto;
		font-size: 0.46rem;
		font-weight: 700;
		letter-spacing: 0.11em;
		text-transform: uppercase;
		color: var(--muted);
	}

	.trace-file a {
		overflow: hidden;
		border-bottom: 1px solid var(--line-strong);
		font-weight: 700;
		text-decoration: none;
		text-overflow: ellipsis;
		white-space: nowrap;
		color: var(--ink);
	}

	.trace-file a:hover {
		border-bottom-color: var(--ink);
	}

	.trace-flow {
		display: flex;
		flex: 1 1 auto;
		align-items: center;
		gap: 9px;
		min-width: 0;
		overflow: hidden;
		padding: 0 16px;
	}

	.trace-cell {
		flex: 0 0 auto;
		background: var(--yellow);
		padding: 3px 7px;
		font-weight: 700;
		color: var(--ink);
	}

	.trace-section,
	.trace-hint {
		flex: 0 1 auto;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		color: var(--muted);
	}

	.trace-arrow {
		flex: 0 0 auto;
		color: var(--yellow-dark);
	}

	.trace-path {
		flex: 0 1 auto;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		color: var(--muted-strong);
	}

	.trace-path i {
		padding: 0 5px;
		font-style: normal;
		color: var(--line-strong);
	}

	.trace-path em {
		font-style: normal;
		font-weight: 700;
		color: var(--ink);
	}

	.trace-value {
		flex: 0 0 auto;
		border-left: 1px solid var(--line);
		padding-left: 10px;
		font-weight: 700;
		color: var(--ink);
	}

	.split {
		display: grid;
		flex: 1 1 auto;
		grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
		gap: 1px;
		min-height: 0;
		background: var(--line);
	}

	.pane {
		display: flex;
		flex-direction: column;
		min-width: 0;
		min-height: 0;
		background: var(--paper);
	}

	.pane-head {
		display: flex;
		flex: 0 0 auto;
		align-items: center;
		justify-content: space-between;
		gap: 14px;
		min-height: 42px;
		border-bottom: 1px solid var(--line);
		background: var(--paper);
		padding: 7px 14px;
	}

	.pane-head h2 {
		margin: 0;
		font-family: var(--font-display);
		font-size: 0.8rem;
		font-weight: 750;
		letter-spacing: 0.02em;
		white-space: nowrap;
		color: var(--ink);
	}

	.pane-tools {
		display: flex;
		flex: 0 1 auto;
		align-items: center;
		gap: 14px;
		min-width: 0;
		overflow: hidden;
	}

	.dataset-tabs {
		display: flex;
		flex: 0 1 auto;
		overflow-x: auto;
		border: 1px solid var(--line-strong);
		background: var(--paper-deep);
	}

	.dataset-tabs button {
		border: 0;
		border-right: 1px solid var(--line);
		background: transparent;
		padding: 6px 11px;
		font-family: var(--font-mono);
		font-size: 0.58rem;
		font-weight: 750;
		white-space: nowrap;
		color: var(--muted);
		cursor: pointer;
	}

	.dataset-tabs button:last-child {
		border-right: 0;
	}

	.dataset-tabs button:hover {
		color: var(--ink);
	}

	.dataset-tabs button.active {
		background: var(--ink);
		color: var(--paper);
	}

	.zoom {
		display: flex;
		flex: 0 0 auto;
		align-items: center;
		border: 1px solid var(--line-strong);
		background: var(--paper-deep);
		font-family: var(--font-mono);
	}

	.zoom button {
		border: 0;
		background: transparent;
		padding: 5px 8px;
		font-size: 0.6rem;
		font-weight: 750;
		line-height: 1;
		color: var(--muted-strong);
		cursor: pointer;
	}

	.zoom button:hover:not(:disabled) {
		color: var(--ink);
	}

	.zoom button:disabled {
		opacity: 0.4;
		cursor: default;
	}

	.zoom output {
		min-width: 42px;
		padding: 0 2px;
		text-align: center;
		font-size: 0.53rem;
		font-weight: 700;
		color: var(--muted-strong);
	}

	.zoom .fit.active {
		background: var(--ink);
		color: var(--paper);
	}

	.pane-body {
		flex: 1 1 auto;
		min-height: 0;
		overflow: auto;
		overscroll-behavior: contain;
	}

	.pane-body.sheet {
		background: var(--paper-deep);
	}

	@media (max-width: 1000px) {
		.workbook-shell {
			height: auto;
			min-height: 100vh;
		}

		.split {
			grid-template-columns: minmax(0, 1fr);
			gap: 0;
		}

		.pane-body {
			max-height: 62vh;
		}
	}

	@media (max-width: 760px) {
		.trace-file,
		.trace-flow {
			padding: 0 12px;
		}

		.trace-path,
		.trace-section {
			display: none;
		}

		.pane-head {
			align-items: stretch;
			flex-direction: column;
			gap: 8px;
		}

		.pane-tools {
			flex-wrap: wrap;
			gap: 10px;
		}
	}
</style>
