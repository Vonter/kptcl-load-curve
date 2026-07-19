export const chartColors = {
	green: '#1d7551',
	yellow: '#c38a10',
	red: '#b8473e',
	blue: '#2b6681',
	ink: '#24332c',
	grey: '#8a938d'
};

const contributorColors = [
	'#1d7551',
	'#2b6681',
	'#c38a10',
	'#b8473e',
	'#6d5b8c',
	'#2a8d8d',
	'#a45e2e',
	'#647067'
];

export function formatDate(value: string, compact = false): string {
	if (!value) return '—';
	return new Date(`${value}T00:00:00`).toLocaleDateString(
		'en-IN',
		compact
			? { day: '2-digit', month: 'short', year: '2-digit' }
			: { day: '2-digit', month: 'short', year: 'numeric' }
	);
}

export function formatNumericDate(value: string | null | undefined): string {
	if (!value) return '—';
	const [year, month, day] = value.split('-');
	return year && month && day ? `${day}-${month}-${year}` : '—';
}

export function formatNumber(value: number | null | undefined, digits = 1): string {
	if (value === null || value === undefined || !Number.isFinite(value)) return '—';
	return value.toLocaleString('en-IN', {
		maximumFractionDigits: digits,
		minimumFractionDigits: 0
	});
}

export function formatHz(value: number): string {
	return value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 3 });
}

export function formatHour(value: string | number): string {
	const hour = Number(value) % 24;
	const suffix = hour < 12 ? 'AM' : 'PM';
	const displayHour = hour % 12 || 12;
	return `${displayHour}${suffix}`;
}

export function oneYearAgo(value: string): string {
	const date = new Date(`${value}T00:00:00`);
	date.setFullYear(date.getFullYear() - 1);
	return date.toISOString().slice(0, 10);
}

export function formatCompact(value: number | null | undefined): string {
	if (value === null || value === undefined || !Number.isFinite(value)) return '—';
	return new Intl.NumberFormat('en-IN', { notation: 'compact', maximumFractionDigits: 1 }).format(
		value
	);
}

export function sliceRange<T extends { date: string }>(
	rows: T[],
	range: string,
	endDate?: string
): T[] {
	if (!rows?.length) return rows ?? [];
	const availableRows = endDate ? rows.filter((row) => row.date <= endDate) : rows;
	if (range === 'ALL' || !availableRows.length) return availableRows;
	const days: Record<string, number> = {
		'7D': 7,
		'14D': 14,
		'30D': 30,
		'6M': 183,
		'1Y': 365,
		'5Y': 1826
	};
	const cutoff = new Date(`${endDate ?? availableRows.at(-1)!.date}T00:00:00`);
	cutoff.setDate(cutoff.getDate() - (days[range] ?? 365));
	const cutoffIso = cutoff.toISOString().slice(0, 10);
	return availableRows.filter((row) => row.date >= cutoffIso);
}

export function labelSection(value: string): string {
	return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function systemLabel(value: string): string {
	return value.replaceAll('_', ' ');
}

export function seriesFor(names: string[]) {
	return names.map((name, index) => ({
		key: name,
		label: name.replace('NCE - ', ''),
		color: contributorColors[index % contributorColors.length]
	}));
}
