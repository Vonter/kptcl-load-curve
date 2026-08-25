<script lang="ts">
	/* eslint-disable svelte/no-navigation-without-resolve -- dataset files live on the data host. */
	import { onMount } from 'svelte';
	import DashboardHeader from '$lib/components/DashboardHeader.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import LoadState from '$lib/components/LoadState.svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { dataUrl, loadDownloads } from '$lib/data/loaders';
	import type { DownloadCatalog, PreviewValue } from '$lib/data/types';
	import { displayValue } from '$lib/data/workbook';

	const BYTE_UNITS = ['B', 'KB', 'MB', 'GB'];

	let catalog = $state<DownloadCatalog | null>(null);
	let selectedId = $state('');
	let loadingError = $state('');
	let selected = $derived(
		catalog?.datasets.find((dataset) => dataset.id === selectedId) ?? catalog?.datasets[0] ?? null
	);

	function size(bytes: number): string {
		let value = bytes;
		let unit = 0;
		while (value >= 1024 && unit < BYTE_UNITS.length - 1) {
			value /= 1024;
			unit += 1;
		}
		return `${value.toFixed(unit > 1 ? 1 : 0)} ${BYTE_UNITS[unit]}`;
	}

	/** Blank cells read as an em dash, midnight timestamps as plain dates. */
	const display = (value: PreviewValue) => displayValue(value).replace('T00:00:00', '') || '—';

	onMount(() => {
		void loadDownloads()
			.then((loaded) => (catalog = loaded))
			.catch((error) => {
				loadingError = error instanceof Error ? error.message : 'Could not load download catalog';
			});
	});
</script>

<SEO
	title="Download data"
	description="Preview and download the complete KPTCL load-curve archive as Parquet or zipped CSV datasets."
/>

<div class="download-shell">
	<DashboardHeader activeReport="download" />

	{#if catalog && selected}
		<div class="split">
			<aside class="dataset-panel">
				<nav aria-label="Dataset">
					{#each catalog.datasets as dataset (dataset.id)}
						<button
							type="button"
							class:active={dataset.id === selected.id}
							onclick={() => (selectedId = dataset.id)}
						>
							{dataset.label}
						</button>
					{/each}
				</nav>
			</aside>

			<section class="preview-pane">
				<div class="pane-head">
					<h2>{selected.label}</h2>
					<div class="download-actions">
						<a
							class="format-button"
							href={dataUrl(`downloads/${selected.parquet.file}`)}
							download={selected.parquet.file}
						>
							<Icon name="download" size={16} />
							<span><strong>Parquet</strong><small>{size(selected.parquet.bytes)}</small></span>
						</a>
						{#if selected.csv}
							<a
								class="format-button"
								href={dataUrl(`downloads/${selected.csv.file}`)}
								download={selected.csv.file}
							>
								<Icon name="download" size={16} />
								<span><strong>CSV</strong><small>{size(selected.csv.bytes)}</small></span>
							</a>
						{:else}
							<span class="format-button unavailable" title="Nested rows are Parquet-only">
								<span><strong>CSV</strong><small>Unavailable</small></span>
							</span>
						{/if}
					</div>
				</div>

				<div class="pane-body">
					<table>
						<thead>
							<tr>
								<th class="row-index"><span class="visually-hidden">Row</span></th>
								{#each selected.columns as column (column.name)}
									<th title={column.type}>{column.name}</th>
								{/each}
							</tr>
						</thead>
						<tbody>
							{#each selected.preview as row, rowIndex (rowIndex)}
								<tr>
									<td class="row-index">{rowIndex + 1}</td>
									{#each selected.columns as column (column.name)}
										{@const text = display(row[column.name] ?? null)}
										<td title={text}>{text}</td>
									{/each}
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</section>
		</div>
	{:else if loadingError}
		<LoadState error={loadingError} title="Download catalog unavailable" />
	{:else}
		<LoadState />
	{/if}
</div>

<style>
	.download-shell {
		display: flex;
		flex-direction: column;
		height: 100vh;
		min-width: 0;
	}

	.download-shell > :global(header) {
		flex: 0 0 auto;
	}

	.split {
		--top-row-height: 55px;
		display: grid;
		flex: 1 1 auto;
		grid-template-columns: 250px minmax(0, 1fr);
		gap: 1px;
		min-height: 0;
		background: var(--line);
	}

	.dataset-panel {
		min-width: 0;
		overflow-y: auto;
		background: var(--paper-deep);
	}

	.dataset-panel nav {
		display: grid;
	}

	.dataset-panel button {
		display: block;
		height: var(--top-row-height);
		border: 0;
		border-bottom: 1px solid var(--line);
		background: transparent;
		padding: 15px 16px;
		font-family: var(--font-display);
		font-size: 1.06rem;
		letter-spacing: -0.015em;
		text-align: left;
		color: var(--muted-strong);
		cursor: pointer;
	}

	.dataset-panel button:hover,
	.dataset-panel button.active {
		background: var(--paper);
		color: var(--ink);
	}

	.preview-pane {
		display: flex;
		flex-direction: column;
		min-width: 0;
		min-height: 0;
		background: var(--paper);
	}

	.pane-head {
		display: flex;
		flex: 0 0 auto;
		height: var(--top-row-height);
		align-items: center;
		justify-content: space-between;
		gap: 14px;
		border-bottom: 1px solid var(--line);
		padding: 8px 14px;
	}

	.pane-head h2 {
		margin: 0;
		overflow: hidden;
		font-family: var(--font-display);
		font-size: 1.5rem;
		letter-spacing: -0.025em;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.visually-hidden {
		position: absolute;
		width: 1px;
		height: 1px;
		overflow: hidden;
		clip-path: inset(50%);
		white-space: nowrap;
	}

	.download-actions {
		display: flex;
		flex: 0 0 auto;
		gap: 8px;
	}

	.format-button {
		display: flex;
		align-items: center;
		gap: 8px;
		border: 1px solid var(--line-strong);
		background: var(--paper);
		padding: 6px 10px;
		text-decoration: none;
		color: var(--ink);
		transition:
			border-color 150ms ease,
			transform 150ms ease;
	}

	.format-button:hover {
		border-color: var(--ink);
		transform: translateY(-1px);
	}

	.format-button span,
	.format-button strong,
	.format-button small {
		display: block;
	}

	.format-button strong {
		font-family: var(--font-mono);
		font-size: 0.6rem;
		text-transform: uppercase;
	}

	.format-button small {
		margin-top: 2px;
		font-family: var(--font-mono);
		font-size: 0.48rem;
		opacity: 0.65;
	}

	.format-button.unavailable {
		border-style: dashed;
		color: var(--muted);
	}

	.pane-body {
		flex: 1 1 auto;
		min-height: 0;
		overflow: auto;
		overscroll-behavior: contain;
		background: white;
	}

	table {
		width: max-content;
		min-width: 100%;
		border-collapse: collapse;
		text-align: left;
	}

	th,
	td {
		max-width: 300px;
		border-right: 1px solid var(--line);
		border-bottom: 1px solid var(--line);
		padding: 8px 11px;
		white-space: nowrap;
	}

	th:last-child,
	td:last-child {
		border-right: 0;
	}

	th {
		position: sticky;
		top: 0;
		z-index: 2;
		background: var(--paper-deep);
		box-shadow: inset 0 -1px var(--line-strong);
		font-family: var(--font-display);
		font-size: 0.68rem;
		letter-spacing: 0.03em;
	}

	.row-index {
		position: sticky;
		left: 0;
		z-index: 1;
		width: 1%;
		border-right: 1px solid var(--line-strong);
		padding-inline: 9px;
		background: var(--paper-deep);
		font-family: var(--font-mono);
		font-size: 0.5rem;
		text-align: right;
		color: var(--muted);
	}

	th.row-index {
		z-index: 3;
	}

	td {
		overflow: hidden;
		font-family: var(--font-mono);
		font-size: 0.58rem;
		text-overflow: ellipsis;
		color: var(--muted-strong);
	}

	/* Keeps a thousand rows cheap to render without giving up native scrolling. */
	tbody tr {
		content-visibility: auto;
		contain-intrinsic-size: auto 30px;
	}

	tbody tr:hover td {
		background: color-mix(in srgb, var(--yellow) 7%, transparent);
	}

	@media (max-width: 900px) {
		.download-shell {
			height: auto;
			min-height: 100vh;
		}

		.split {
			grid-template-columns: minmax(0, 1fr);
			gap: 0;
		}

		.dataset-panel {
			border-bottom: 1px solid var(--line);
		}

		.dataset-panel nav {
			display: flex;
			overflow-x: auto;
		}

		.dataset-panel button {
			min-width: 190px;
			border-right: 1px solid var(--line);
			border-bottom: 0;
		}

		.pane-body {
			max-height: 70vh;
		}
	}

	@media (max-width: 620px) {
		.pane-head {
			align-items: flex-start;
			flex-direction: column;
			gap: 8px;
			height: auto;
		}

		.download-actions {
			width: 100%;
		}

		.format-button {
			flex: 1 1 0;
		}
	}
</style>
