export type ReportId =
	'load' | 'stations' | 'reservoirs' | 'outages' | 'summary' | 'historical' | 'sections';

export const reports: { id: ReportId; number: string; label: string }[] = [
	{ id: 'load', number: '01', label: 'System Load' },
	{ id: 'stations', number: '02', label: 'Generation' },
	{ id: 'reservoirs', number: '03', label: 'Reservoirs' },
	{ id: 'outages', number: '04', label: 'Outages' },
	{ id: 'summary', number: '05', label: 'Daily' },
	{ id: 'historical', number: '06', label: 'Historical' },
	{ id: 'sections', number: '07', label: 'Meta' }
];

export function isReportId(value: string | null): value is ReportId {
	return reports.some((report) => report.id === value);
}
