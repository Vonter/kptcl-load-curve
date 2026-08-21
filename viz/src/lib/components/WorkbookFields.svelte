<script lang="ts">
	import type { WorkbookDataset } from '$lib/data/types';
	import { displayValue, isNumericValue, type Selection } from '$lib/data/workbook';

	let {
		dataset,
		selection,
		onPick
	}: {
		dataset: WorkbookDataset;
		selection: Selection | null;
		onPick: (recordIndex: number, field: string) => void;
	} = $props();

	function isSelected(recordIndex: number, field: string): boolean {
		return (
			selection?.datasetId === dataset.id &&
			selection.recordIndex === recordIndex &&
			selection.field === field
		);
	}
</script>

<table>
	<thead>
		<tr>
			<th scope="col" class="key">{dataset.key}</th>
			{#each dataset.fields as field (field)}
				<th scope="col">{field}</th>
			{/each}
		</tr>
	</thead>
	<tbody>
		{#each dataset.records as record, recordIndex (recordIndex)}
			<tr class:kin={selection?.datasetId === dataset.id && selection.recordIndex === recordIndex}>
				<th scope="row">{record.label}</th>
				{#each dataset.fields as field (field)}
					{@const value = record.values[field] ?? null}
					{@const addresses = record.cells[field] ?? []}
					<td
						data-key="{recordIndex}:{field}"
						class:numeric={isNumericValue(value)}
						class:selected={isSelected(recordIndex, field)}
						class:untraced={addresses.length === 0}
					>
						{#if addresses.length > 0}
							<button
								type="button"
								title="{field} = {displayValue(value)}&#10;from {addresses.join(', ')}"
								onclick={() => onPick(recordIndex, field)}
							>
								<span class="text">{displayValue(value) || '—'}</span>
								<span class="address">{addresses.join(' ')}</span>
							</button>
						{:else}
							<span class="text plain" title="Not traced to a single cell"
								>{displayValue(value) || '—'}</span
							>
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
		width: 100%;
		font-family: var(--font-mono);
		font-size: 0.6rem;
		color: var(--ink);
	}

	th,
	td {
		border-right: 1px solid var(--line);
		border-bottom: 1px solid var(--line);
		white-space: nowrap;
	}

	thead th {
		position: sticky;
		top: 0;
		z-index: 3;
		background: var(--paper-deep);
		padding: 7px 8px;
		text-align: left;
		font-size: 0.5rem;
		font-weight: 750;
		letter-spacing: 0.03em;
		color: var(--muted-strong);
	}

	tbody th {
		position: sticky;
		left: 0;
		z-index: 2;
		max-width: 190px;
		overflow: hidden;
		background: var(--paper-deep);
		padding: 0 9px;
		text-align: left;
		font-family: var(--font-display);
		font-size: 0.68rem;
		font-weight: 750;
		text-overflow: ellipsis;
		color: var(--ink);
	}

	thead th.key {
		position: sticky;
		left: 0;
		z-index: 4;
	}

	td {
		height: 27px;
		max-width: 250px;
		overflow: hidden;
		background: var(--paper);
		padding: 0;
	}

	td button,
	td .plain {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
		width: 100%;
		height: 27px;
		border: 0;
		background: transparent;
		padding: 0 8px;
		font: inherit;
		text-align: left;
		color: inherit;
	}

	td button {
		cursor: pointer;
	}

	td.numeric button,
	td.numeric .plain {
		flex-direction: row-reverse;
	}

	.text {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.address {
		flex: 0 0 auto;
		font-size: 0.48rem;
		letter-spacing: 0.02em;
		color: var(--muted);
		opacity: 0;
		transition: opacity 120ms ease;
	}

	td button:hover {
		background: color-mix(in srgb, var(--yellow) 22%, var(--paper));
	}

	td button:hover .address {
		opacity: 1;
	}

	tr.kin td:not(.selected) {
		background: color-mix(in srgb, var(--blue) 8%, var(--paper));
	}

	tr.kin th {
		background: color-mix(in srgb, var(--blue) 15%, var(--paper-deep));
	}

	td.selected {
		background: var(--yellow);
	}

	td.selected button {
		font-weight: 700;
	}

	td.selected .address {
		opacity: 1;
		font-weight: 700;
		color: var(--ink);
	}

	td.untraced .plain {
		font-style: italic;
		color: var(--muted);
	}
</style>
