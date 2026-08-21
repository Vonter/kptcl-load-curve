<script lang="ts">
	import type { WorkbookCell } from '$lib/data/types';
	import { columnName, displayValue, isNumericValue } from '$lib/data/workbook';
	import { labelSection } from '$lib/reports/reportUtils';

	let {
		cells,
		rows,
		columns,
		mapped,
		kin,
		hit,
		onPick
	}: {
		cells: WorkbookCell[];
		rows: number;
		columns: number;
		mapped: Set<string>;
		kin: Set<string>;
		hit: Set<string>;
		onPick: (address: string) => void;
	} = $props();

	let grid = $derived.by(() => {
		const sheet: (WorkbookCell | null)[][] = Array.from({ length: rows }, () =>
			Array.from({ length: columns }, () => null)
		);
		for (const cell of cells) sheet[cell.r][cell.c] = cell;
		return sheet;
	});

	let headers = $derived(Array.from({ length: columns }, (_, index) => columnName(index)));

	function tooltip(address: string, cell: WorkbookCell | null): string {
		if (!cell) return `${address}\n(blank)`;
		const value = displayValue(cell.v, cell.t);
		const section = cell.s ? `\n${labelSection(cell.s)}` : '';
		return `${address}\n${value}${section}`;
	}
</script>

<table style="--column-count: {columns}">
	<thead>
		<tr>
			<th class="corner" scope="col"><span class="sr-only">Row</span></th>
			{#each headers as header, index (header)}
				<th scope="col" class:live={index < columns}>{header}</th>
			{/each}
		</tr>
	</thead>
	<tbody>
		{#each grid as row, rowIndex (rowIndex)}
			<tr>
				<th scope="row">{rowIndex + 1}</th>
				{#each row as cell, columnIndex (columnIndex)}
					{@const address = cell?.a ?? `${headers[columnIndex]}${rowIndex + 1}`}
					{@const traced = mapped.has(address)}
					<td
						data-address={address}
						class:traced
						class:kin={kin.has(address)}
						class:hit={hit.has(address)}
						class:numeric={cell ? isNumericValue(cell.v) : false}
						class:filled={Boolean(cell)}
					>
						{#if traced}
							<button type="button" title={tooltip(address, cell)} onclick={() => onPick(address)}>
								{cell ? displayValue(cell.v, cell.t) : ''}
							</button>
						{:else if cell}
							<span title={tooltip(address, cell)}>{displayValue(cell.v, cell.t)}</span>
						{/if}
					</td>
				{/each}
			</tr>
		{/each}
	</tbody>
</table>

<style>
	table {
		border-collapse: separate;
		border-spacing: 0;
		table-layout: fixed;
		width: calc(46px + var(--column-count) * 92px);
		font-family: var(--font-mono);
		font-size: 0.58rem;
		color: var(--ink);
	}

	th,
	td {
		overflow: hidden;
		height: 23px;
		max-width: 92px;
		border-right: 1px solid var(--line);
		border-bottom: 1px solid var(--line);
		padding: 0;
		white-space: nowrap;
	}

	thead th {
		position: sticky;
		top: 0;
		z-index: 3;
		width: 92px;
		background: var(--paper-deep);
		font-size: 0.5rem;
		font-weight: 750;
		letter-spacing: 0.05em;
		color: var(--muted);
	}

	tbody th {
		position: sticky;
		left: 0;
		z-index: 2;
		width: 46px;
		background: var(--paper-deep);
		text-align: right;
		padding-right: 5px;
		font-size: 0.5rem;
		font-weight: 700;
		color: var(--muted);
	}

	.corner {
		position: sticky;
		left: 0;
		z-index: 4;
		width: 46px;
	}

	td {
		background: var(--paper);
	}

	td.filled span,
	td button {
		display: block;
		width: 100%;
		overflow: hidden;
		padding: 0 5px;
		text-align: left;
		text-overflow: ellipsis;
		white-space: nowrap;
		line-height: 22px;
	}

	td.numeric span,
	td.numeric button {
		text-align: right;
	}

	td button {
		border: 0;
		background: transparent;
		font: inherit;
		color: inherit;
		cursor: pointer;
	}

	td.traced {
		background: color-mix(in srgb, var(--yellow) 13%, var(--paper));
	}

	td.traced:hover {
		background: color-mix(in srgb, var(--yellow) 30%, var(--paper));
	}

	td.kin {
		background: color-mix(in srgb, var(--blue) 20%, var(--paper));
	}

	td.kin:hover {
		background: color-mix(in srgb, var(--blue) 32%, var(--paper));
	}

	td.hit {
		position: relative;
		z-index: 1;
		background: var(--yellow);
		box-shadow: inset 0 0 0 2px var(--ink);
	}

	td.hit button {
		font-weight: 700;
	}

	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		overflow: hidden;
		clip-path: inset(50%);
		white-space: nowrap;
	}
</style>
