import { base } from '$app/paths';
import type { DashboardData, DateReports, HistoricalData, WorkbookData } from './types';

const reportYears = new Map<string, DateReports>();

async function loadJson<T>(path: string, label: string): Promise<T> {
	const response = await fetch(`${base}/data/${path}`);
	if (!response.ok) throw new Error(`${label} request failed (${response.status})`);
	return response.json() as Promise<T>;
}

export const loadDashboard = () => loadJson<DashboardData>('dashboard.json', 'Data');
export const loadHistorical = () => loadJson<HistoricalData>('historical.json', 'Historical data');
export const loadWorkbook = () => loadJson<WorkbookData>('workbook.json', 'Workbook data');

async function loadReportYear(year: string): Promise<DateReports> {
	const cached = reportYears.get(year);
	if (cached) return cached;
	const { dates } = await loadJson<{ dates: DateReports }>(`reports/${year}.json`, 'Report data');
	reportYears.set(year, dates);
	return dates;
}

export async function loadReportYears(date: string, firstDate: string): Promise<DateReports> {
	const year = Number(date.slice(0, 4));
	const firstYear = Number(firstDate.slice(0, 4));
	const years = [String(year), ...(year > firstYear ? [String(year - 1)] : [])];
	const archives = await Promise.all(years.map(loadReportYear));
	return Object.assign({}, ...archives.toReversed()) as DateReports;
}

export function nearestDate(value: string, dates: string[]): string {
	let low = 0;
	let high = dates.length - 1;
	while (low <= high) {
		const middle = Math.floor((low + high) / 2);
		if (dates[middle] === value) return value;
		if (dates[middle] < value) low = middle + 1;
		else high = middle - 1;
	}
	return dates[Math.max(0, high)] ?? '';
}
