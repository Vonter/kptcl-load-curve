export type NullableNumber = number | null;
export type ChartDatum = Record<string, string | number | null>;
export type PreviewValue = string | number | boolean | null;

export interface DownloadFile {
	file: string;
	bytes: number;
}

export interface DownloadDataset {
	id: string;
	label: string;
	description: string;
	rows: number;
	columns: { name: string; type: string }[];
	parquet: DownloadFile;
	csv: DownloadFile | null;
	preview: Record<string, PreviewValue>[];
}

export interface DownloadCatalog {
	datasets: DownloadDataset[];
}

export interface LoadPoint extends ChartDatum {
	hour: number;
	load: NullableNumber;
	frequency: NullableNumber;
}

export interface LoadDay extends ChartDatum {
	date: string;
	peak: NullableNumber;
	minimum: NullableNumber;
	average: NullableNumber;
	peakHour: number;
	minimumHour: number;
	minHz: NullableNumber;
	maxHz: NullableNumber;
	averageHz: NullableNumber;
}

export interface StationAsset extends ChartDatum {
	station: string;
	category: string;
	capacity: NullableNumber;
	units: NullableNumber;
	generation: NullableNumber;
	energy: NullableNumber;
	previousEnergy: NullableNumber;
	yearAgoEnergy: NullableNumber;
}

export interface StationDay extends ChartDatum {
	date: string;
	capacity: NullableNumber;
	energy: NullableNumber;
	maximum: NullableNumber;
	minimum: NullableNumber;
}

export interface StationTotals {
	capacity: NullableNumber;
	energy: NullableNumber;
	maximum: NullableNumber;
}

export interface StationSnapshot {
	totals: StationTotals;
	assets: StationAsset[];
	contributors: { nce: string[]; other: string[] };
}

export interface ReservoirDay extends ChartDatum {
	date: string;
	reservoir: string;
	storage: NullableNumber;
	previousStorage: NullableNumber;
	inflow: NullableNumber;
	discharge: NullableNumber;
	energy: NullableNumber;
	level: NullableNumber;
	fullLevel: NullableNumber;
	levelUnit: string | null;
}

export interface OutageDay extends ChartDatum {
	date: string;
	total: number;
	planned: number;
	forced: number;
	lines: number;
}

export interface DashboardOutageDay extends OutageDay {
	regulation: number;
}

export interface OutageEvent {
	system: string;
	type: string;
	asset: string;
	details: string | null;
	from: string | null;
	to: string | null;
	remarks: string | null;
}

export interface SummaryMetric extends ChartDatum {
	entity: string;
	value: NullableNumber;
	unit: string | null;
}

export interface ExchangeMetric extends SummaryMetric {
	metric: string;
}

export interface SummaryDay extends ChartDatum {
	date: string;
	energy: NullableNumber;
	maximumDemand: NullableNumber;
	minimumDemand: NullableNumber;
	maximumFrequency: NullableNumber;
	minimumFrequency: NullableNumber;
}

export interface SectionTotal {
	section: string;
	reports: number;
	first: string;
	last: string;
	cells: number;
	byYear: number[];
}

export interface SectionSnapshot {
	section: string;
	rows: number;
	cells: number;
}

export interface DashboardData {
	reportDates: string[];
	load: {
		coverage: string[];
		observations: number;
		daily: LoadDay[];
		curve: Record<string, LoadPoint[]>;
	};
	stations: {
		coverage: string[];
		reportDate: string;
		previousDate: string;
		history: StationDay[];
		totals: StationTotals;
		assets: StationAsset[];
		contributors: { nce: string[]; other: string[]; history: ChartDatum[] };
	};
	reservoirs: {
		coverage: string[];
		reportDate: string;
		reservoirs: string[];
		history: ReservoirDay[];
	};
	outages: {
		coverage: string[];
		reportDate: string;
		history: DashboardOutageDay[];
		events: OutageEvent[];
	};
	summary: {
		coverage: string[];
		reportDate: string;
		reportDates: number;
		curve: LoadPoint[];
		grid: SummaryDay[];
		generation: SummaryMetric[];
		exchange: ExchangeMetric[];
	};
	sections: {
		coverage: string[];
		reportDate: string;
		years: number[];
		history: ChartDatum[];
		sections: SectionTotal[];
		latest: SectionSnapshot[];
	};
}

export interface ReportSnapshot {
	load: { curve: LoadPoint[] };
	stations: StationSnapshot;
	outages: { events: OutageEvent[] };
	summary: {
		available: boolean;
		generation: SummaryMetric[];
		exchange: ExchangeMetric[];
	};
	sections: { latest: SectionSnapshot[] };
}

export type DateReports = Record<string, ReportSnapshot>;

export type WorkbookCellType = 'text' | 'number' | 'date' | 'boolean' | 'error' | 'unknown';

export interface WorkbookCell {
	/** Excel address, such as `AJ5`. */
	a: string;
	/** Zero-based row index. */
	r: number;
	/** Zero-based column index. */
	c: number;
	t: WorkbookCellType;
	v: string | number | boolean;
	/** Parsed section the cell belongs to, when it falls inside one. */
	s?: string;
}

export interface WorkbookRecord {
	label: string;
	values: Record<string, string | number | null>;
	cells: Record<string, string[]>;
}

export interface WorkbookDataset {
	id: string;
	label: string;
	table: string;
	note: string;
	key: string;
	fields: string[];
	records: WorkbookRecord[];
}

export interface WorkbookData {
	reportDate: string;
	workbook: string;
	sourceUrl: string;
	sheet: { name: string; rows: number; columns: number };
	cells: WorkbookCell[];
	mappedCells: number;
	datasets: WorkbookDataset[];
}

export interface HistoricalData {
	coverage: [string, string];
	load: LoadDay[];
	generation: StationDay[];
	generationSources: { names: string[]; history: ChartDatum[] };
	reservoirs: { names: string[]; history: ChartDatum[] };
	outages: OutageDay[];
}
