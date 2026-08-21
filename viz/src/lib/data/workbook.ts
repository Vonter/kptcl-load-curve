import type { WorkbookCellType, WorkbookDataset } from './types';

/** One traced value: which record of which dataset, and which of its fields. */
export interface Selection {
	datasetId: string;
	recordIndex: number;
	field: string;
}

export function columnName(index: number): string {
	let name = '';
	for (let value = index; value >= 0; value = Math.floor(value / 26) - 1) {
		name = String.fromCharCode(65 + (value % 26)) + name;
	}
	return name;
}

/** Drop binary float noise (9263.185000000001) without hiding real precision. */
function exactNumber(value: number): string {
	return Number.isFinite(value) ? String(Number(value.toPrecision(12))) : String(value);
}

export function displayValue(
	value: string | number | boolean | null,
	type: WorkbookCellType = 'text'
): string {
	if (value === null || value === undefined || value === '') return '';
	if (typeof value === 'number') return exactNumber(value);
	if (typeof value === 'boolean') return value ? 'TRUE' : 'FALSE';
	if (type === 'date') return value.replace('T', ' ').replace(/:00$/, '');
	return value;
}

export function isNumericValue(value: unknown): boolean {
	return typeof value === 'number';
}

/** Map every source address to the dataset fields it feeds. */
export function buildOriginIndex(datasets: WorkbookDataset[]): Map<string, Selection[]> {
	const index = new Map<string, Selection[]>();
	for (const dataset of datasets) {
		dataset.records.forEach((record, recordIndex) => {
			for (const [field, addresses] of Object.entries(record.cells)) {
				for (const address of addresses) {
					const origin = { datasetId: dataset.id, recordIndex, field };
					const origins = index.get(address);
					if (origins) origins.push(origin);
					else index.set(address, [origin]);
				}
			}
		});
	}
	return index;
}

export function recordAddresses(dataset: WorkbookDataset, recordIndex: number): string[] {
	return Object.values(dataset.records[recordIndex]?.cells ?? {}).flat();
}
