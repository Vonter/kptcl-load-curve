"""Build the cell-level payload for the /workbook page.

Raw workbooks are not committed, runs on demand:

    uv run --project .. python scripts/build_workbook.py [--date YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import xlrd
from xlrd.formula import colname

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import parse  # noqa: E402  (repo-root parser, imported after the path is set)

DATA_DIR = ROOT / "data"
RAW_DIR = ROOT / "raw"
OUTPUT = ROOT / "viz" / "static" / "data" / "workbook.json"

SOURCE_URL = "https://loadcurve.kptcl.net/LoadCurveUpload/lcdownloadview.asp"


@dataclass
class Record:
	"""One dataset row, with the workbook cells each of its values came from."""

	label: str
	values: dict[str, Any] = field(default_factory=dict)
	cells: dict[str, list[str]] = field(default_factory=dict)

	def set(self, name: str, value: Any, *cells: str | None) -> None:
		self.values[name] = value
		addresses = [cell for cell in cells if cell]
		if addresses:
			self.cells[name] = addresses


def address(row: int, col: int) -> str:
	return f"{colname(col)}{row + 1}"


def trace_load_curve(day: date, sheet: parse.SheetView) -> list[Record]:
	anchor = parse._load_curve_anchor(sheet)
	if not anchor:
		return []
	header_row, time_col = anchor
	nearby_headers = {
		col: " ".join(
			parse._clean(sheet.cell_value(row, col)).upper()
			for row in range(header_row, min(header_row + 2, sheet.nrows))
		)
		for col in range(time_col, min(time_col + 4, sheet.ncols))
	}
	load_col = next((col for col, header in nearby_headers.items() if "LOAD" in header), time_col + 1)
	frequency_col = next((col for col, header in nearby_headers.items() if "FREQUENCY" in header), None)
	records: list[Record] = []
	seen_hours: set[int] = set()
	for row in range(header_row + 1, min(sheet.nrows, header_row + 32)):
		raw_hour = parse._number(sheet.cell_value(row, time_col))
		if raw_hour is None or not raw_hour.is_integer():
			continue
		hour = int(raw_hour)
		if hour not in range(25) or hour in seen_hours:
			continue
		load = parse._number(sheet.cell_value(row, load_col)) if load_col < sheet.ncols else None
		frequency = (
			parse._number(sheet.cell_value(row, frequency_col)) if frequency_col is not None else None
		)
		if load is None and frequency is None:
			continue
		seen_hours.add(hour)
		record = Record(label=f"{hour:02d}:00")
		record.set("report_hour", hour, address(row, time_col))
		record.set(
			"observed_at",
			(datetime.combine(day, datetime.min.time()) + pd.Timedelta(hours=hour)).isoformat(),
			address(row, time_col),
		)
		record.set("grid_load_mw", load, address(row, load_col) if load_col < sheet.ncols else None)
		record.set(
			"frequency_hz",
			frequency,
			address(row, frequency_col) if frequency_col is not None else None,
		)
		records.append(record)
	return records


def trace_stations(_day: date, sheet: parse.SheetView) -> list[Record]:
	anchor = parse._find(sheet, "STATIONS", exact=True)
	if not anchor:
		return []
	header_row, station_col = anchor
	records: list[Record] = []
	category = "generation and exchanges"
	category_cell: str | None = None
	if station_col > 0 and header_row > 0:
		preceding = parse._clean(sheet.cell_value(header_row - 1, station_col - 1))
		if preceding.endswith((":", ":-")):
			category = re.sub(r"^[A-Z]\.?\s*", "", preceding.rstrip(":- "), flags=re.I)
			category_cell = address(header_row - 1, station_col - 1)
	fields = {
		3: "installed_units",
		4: "installed_capacity_mw",
		5: "units_generating",
		6: "generation_at_state_max_mw",
		7: "generation_at_state_min_mw",
		8: "energy_generated_mu",
		10: "record_max_mw",
	}
	for row in range(header_row + 1, sheet.nrows):
		station = parse._clean(sheet.cell_value(row, station_col))
		station_cell = address(row, station_col)
		left = parse._clean(sheet.cell_value(row, station_col - 1)) if station_col > 0 else ""
		if not station and left.endswith((":", ":-")):
			category = re.sub(r"^[A-Z]\.?\s*", "", left.rstrip(":- "), flags=re.I)
			category_cell = address(row, station_col - 1)
			continue
		if not station and left.upper() in {"TOTAL", "GRAND TOTAL"}:
			station = left
			station_cell = address(row, station_col - 1)
		if not station:
			continue
		upper = station.upper()
		if upper.startswith(("PROJECTION", "ENERGY CONSUMED", "BALANCE AS", "RAINFALL")):
			break
		if upper.endswith((":", ":-")):
			category = station.rstrip(":- ")
			category_cell = station_cell
			continue
		record = Record(label=parse.normalize_station_name(station))
		record.set("category", category, category_cell)
		record.set("station", parse.normalize_station_name(station), station_cell)
		for offset, name in fields.items():
			if station_col + offset < sheet.ncols:
				record.set(
					name,
					parse._station_number(sheet.cell_value(row, station_col + offset)),
					address(row, station_col + offset),
				)
			else:
				record.set(name, None)
		if any(record.values.get(name) is not None for name in fields.values()):
			records.append(record)
		if upper == "GRAND TOTAL":
			break
	return records


def _observed_at_cell(sheet: parse.SheetView) -> str | None:
	for row in range(sheet.nrows):
		for col in range(sheet.ncols):
			text = parse._clean(sheet.cell_value(row, col)).casefold()
			if "reservoir" in text and "details" in text and "hrs" in text:
				return address(row, col)
	return None


def trace_reservoirs(day: date, sheet: parse.SheetView) -> list[Record]:
	anchor = parse._find(sheet, "RESERVOIR", exact=True)
	if not anchor:
		return []
	header_row, label_col = anchor
	installed = parse._find(sheet, "INSTALLED CAPACITY")
	end_row = installed[0] if installed else min(header_row + 17, sheet.nrows)
	canonical_names = {
		"L.MAKKI": "Linganamakki", "L MAKKI": "Linganamakki", "SUPA": "Supa", "MANI": "Mani",
	}
	names: list[tuple[int, str, float | None]] = []
	for col in range(label_col + 1, sheet.ncols):
		text = parse._clean(sheet.cell_value(header_row, col))
		key = next((name for name in canonical_names if name in text.upper()), None)
		if not key:
			continue
		capacity_match = re.search(r"\(([\d,.]+)\s*MU\)", text, re.I)
		names.append((
			col,
			canonical_names[key],
			float(capacity_match.group(1).replace(",", "")) if capacity_match else None,
		))
	observed_at = parse._reservoir_observed_at(day, sheet)
	observed_cell = _observed_at_cell(sheet)
	records = []
	for name_col, name, energy_capacity in names:
		record = Record(label=name)
		record.set("observed_at", observed_at.isoformat() if observed_at else None, observed_cell)
		record.set("reservoir", name, address(header_row, name_col))
		record.set("energy_capacity_mu", energy_capacity, address(header_row, name_col))
		records.append(record)

	for index, (start_col, _name, _energy) in enumerate(names):
		stop_col = names[index + 1][0] if index + 1 < len(names) else min(start_col + 8, sheet.ncols)
		record = records[index]
		for row in range(header_row + 1, end_row):
			label = parse._clean(sheet.cell_value(row, label_col))
			upper = label.upper()
			if upper.startswith("FULL RESERVOIR LEVEL"):
				text = parse._clean(sheet.cell_value(row, start_col))
				value = re.search(r"[-+]?[\d,.]+", text)
				unit = re.search(r"\b(FT|FEET|MTRS?|METERS?)\b", text, re.I)
				cell = address(row, start_col)
				record.set(
					"full_reservoir_level",
					float(value.group().replace(",", "")) if value else None,
					cell,
				)
				record.set("full_reservoir_level_unit", unit.group().lower() if unit else None, cell)
				continue
			if upper.startswith("CAPACITY IN MCFT"):
				text = parse._clean(sheet.cell_value(row, start_col))
				value = re.match(r"[\d,.]+", text)
				record.set(
					"capacity_mcft",
					float(value.group().replace(",", "")) if value else None,
					address(row, start_col),
				)
				continue
			metric = parse._reservoir_metric(label)
			if not metric:
				continue
			found = [
				(col, value)
				for col in range(start_col, stop_col)
				if (value := parse._number(sheet.cell_value(row, col))) is not None
			]
			if not found:
				continue
			record.set(f"previous_year_{metric}", found[0][1], address(row, found[0][0]))
			if len(found) > 1:
				record.set(f"current_{metric}", found[-1][1], address(row, found[-1][0]))
	return records


def _trace_generator_outages(
	sheet: parse.SheetView, system: str, heading: str, stop_headings: tuple[str, ...]
) -> list[Record]:
	anchor = parse._find(sheet, heading)
	if not anchor:
		return []
	heading_row, heading_col = anchor
	header_row = heading_row + 1
	type_columns = []
	for col in range(sheet.ncols):
		header = parse._clean(sheet.cell_value(header_row, col)).casefold()
		if "planned outage" in header:
			type_columns.append((col, "planned"))
		elif "forced outage" in header:
			type_columns.append((col, "forced"))
	records: list[Record] = []
	previous_by_column: dict[int, Record] = {}
	for row in range(header_row + 1, sheet.nrows):
		row_text = sheet.row_text(row)
		if any(stop.casefold() in row_text for stop in stop_headings):
			break
		for col, outage_type in type_columns:
			details = parse._clean(sheet.cell_value(row, col))
			if not details or not re.search(r"[A-Za-z]", details):
				continue
			cell = address(row, col)
			if re.match(r"^(?:[-&]|AND\b|SYN(?:C)?\b)", details, re.I) and col in previous_by_column:
				carried = previous_by_column[col]
				carried.values["details"] += " " + details.lstrip(" -&")
				carried.cells["details"].append(cell)
				continue
			asset = parse._generator_asset(details) or "Unspecified generator"
			record = Record(label=asset)
			record.set("system", system, address(heading_row, heading_col))
			record.set("outage_type", outage_type, address(header_row, col))
			record.set("asset", asset, cell)
			record.set("details", details, cell)
			for name in ("from_time", "to_time", "remarks"):
				record.set(name, None)
			records.append(record)
			previous_by_column[col] = record
	return records


def _trace_line_outages(
	sheet: parse.SheetView, heading: str, outage_type: str, stop_headings: tuple[str, ...]
) -> list[Record]:
	anchor = parse._find(sheet, heading)
	if not anchor:
		return []
	heading_row, heading_col = anchor
	local_header_row = heading_row + 1
	has_local_header = any(
		parse._clean(sheet.cell_value(local_header_row, col)).casefold() == "from"
		for col in range(sheet.ncols)
	)
	shared_header = parse._find(sheet, "Name of the line")
	header_row, asset_col = (
		(local_header_row, heading_col) if has_local_header or not shared_header else shared_header
	)
	first_data_row = local_header_row + 1 if has_local_header else heading_row + 1
	columns = {"asset": asset_col}
	for col in range(asset_col, sheet.ncols):
		header = parse._clean(sheet.cell_value(header_row, col)).casefold()
		if header in {"from", "to", "details", "remarks"}:
			columns[{"from": "from_time", "to": "to_time"}.get(header, header)] = col
	records: list[Record] = []
	for row in range(first_data_row, sheet.nrows):
		row_text = sheet.row_text(row)
		asset = parse._clean(sheet.cell_value(row, columns["asset"]))
		if not asset and any(stop.casefold() in row_text for stop in stop_headings):
			break
		if not asset:
			continue
		record = Record(label=asset)
		record.set("system", "major_line", address(heading_row, heading_col))
		record.set("asset", asset, address(row, columns["asset"]))
		for name in ("details", "from_time", "to_time", "remarks"):
			if name in columns:
				record.set(
					name,
					parse._clean(sheet.cell_value(row, columns[name])) or None,
					address(row, columns[name]),
				)
			else:
				record.set(name, None)
		classification = " ".join(
			parse._clean(record.values.get(name)) for name in ("details", "remarks")
		)
		resolved = outage_type
		if outage_type == "line_clear_or_outage" and re.search(
			r"\b(?:O\s*/?\s*O\s+ON\s+)?(?:OV|PR)\b|OVER\s*VOLT|POWER\s*REG", classification, re.I
		):
			resolved = "over_voltage_or_power_regulation"
		record.set("outage_type", resolved, address(heading_row, heading_col))
		records.append(record)
	return records


def trace_outages(_day: date, sheet: parse.SheetView) -> list[Record]:
	records = _trace_generator_outages(
		sheet, "central_generator", "Central Generator Outages", ("State Generator Outages",)
	)
	records += _trace_generator_outages(
		sheet,
		"state_generator",
		"State Generator Outages",
		("Unscheduled Load Curtailment", "Major Lines (Over Voltage"),
	)
	records += _trace_line_outages(
		sheet, "Major Lines (Line Clears & Outages)", "line_clear_or_outage",
		("State Generator Outages",),
	)
	records += _trace_line_outages(
		sheet, "Major Lines (Over Voltage & Power Regulation)", "over_voltage_or_power_regulation",
		("Rainfall", "Projection"),
	)
	return records


@dataclass(frozen=True)
class Dataset:
	"""How one dataset is traced, and how the page labels it."""

	id: str
	label: str
	key: str
	note: str
	trace: Callable[[date, parse.SheetView], list[Record]]


DATASETS = {
	"load_curve": Dataset(
		"load", "Hourly load", "hour",
		"One row per hour, read down the TIME / LOAD / FREQUENCY block.", trace_load_curve,
	),
	"stations": Dataset(
		"stations", "Stations", "station",
		"One row per generating station, read across the STATIONS block.", trace_stations,
	),
	"reservoirs": Dataset(
		"reservoirs", "Reservoirs", "reservoir",
		"One row per major reservoir, read down the RESERVOIR block.", trace_reservoirs,
	),
	"outages": Dataset(
		"outages", "Outages", "asset",
		"One row per generator or line outage, read from the outage lists.", trace_outages,
	),
}

# ``report_date`` comes from the filename and ``source_station`` is a parse.py
# derivation, so neither has a cell of its own to show on the page.
UNTRACED_COLUMNS = {"report_date", "source_station"}


def fields_of(dataset: str) -> list[str]:
	return [name for name in parse.DEBUG_DATASET_COLUMNS[dataset] if name not in UNTRACED_COLUMNS]


def comparable(value: Any) -> Any:
	if value is None or (isinstance(value, float) and math.isnan(value)):
		return None
	if isinstance(value, float):
		return None if not math.isfinite(value) else round(value, 6)
	if isinstance(value, (int,)) and not isinstance(value, bool):
		return round(float(value), 6)
	if isinstance(value, (pd.Timestamp, datetime)):
		return pd.Timestamp(value).isoformat()
	return str(value)


def _rows_for_comparison(rows: list[dict[str, Any]], names: list[str]) -> list[tuple]:
	"""Normalize rows into a deduplicated, order-independent comparison key.

	Published Parquets are merged and deduplicated across runs, so neither row
	order nor exact duplicates survive from the workbook into the dataset.
	"""
	tuples = {tuple(comparable(row.get(name)) for name in names) for row in rows}
	return sorted(tuples, key=lambda row: tuple(str(value) for value in row))


def verify(dataset: str, records: list[Record], day: date) -> None:
	"""Fail the build if a tracer has drifted away from parse.py."""
	path = DATA_DIR / parse.DATASET_FILES[dataset]
	frame = pd.read_parquet(path)
	frame = frame[frame.report_date == pd.Timestamp(day)]
	names = fields_of(dataset)
	expected = _rows_for_comparison(frame.loc[:, names].to_dict(orient="records"), names)
	traced = _rows_for_comparison([record.values for record in records], names)
	if expected == traced:
		print(f"  {dataset}: {len(records)} rows traced and verified against {path.name}")
		return
	detail = next(
		(
			f"dataset={dict(zip(names, left))} traced={dict(zip(names, right))}"
			for left, right in zip(expected, traced)
			if left != right
		),
		f"distinct row counts differ: dataset={len(expected)} traced={len(traced)}",
	)
	raise SystemExit(
		f"{dataset} provenance does not match {path.name} for {day}. "
		f"The tracer has drifted from parse.py. {detail}"
	)


def cell_payload(sheet: parse.SheetView, row: int, col: int) -> dict[str, Any] | None:
	if not parse._clean(sheet.cell_value(row, col)):
		return None
	cell = parse._json_cell(sheet, row, col)
	return {
		"a": cell["cell"],
		"r": row,
		"c": col,
		"t": cell["type"],
		"v": cell["value"],
	}


def section_lookup(day: date, sheet: parse.SheetView) -> dict[str, str]:
	lookup: dict[str, str] = {}
	for record in parse.parse_sections(day, sheet):
		if record["section"] == "unclassified":
			continue
		for cell in json.loads(record["cells_json"]):
			lookup[cell["cell"]] = record["section"]
	return lookup


def build(day: date, path: Path) -> dict[str, Any]:
	book = xlrd.open_workbook(path)
	if book.nsheets != 1:
		raise SystemExit(
			f"{path.name} has {book.nsheets} sheets. The workbook page renders a single sheet; "
			"pick a single-sheet report with --date."
		)
	sheet = parse.view(book.sheet_by_index(0))

	cells = [
		payload
		for row in range(sheet.nrows)
		for col in range(sheet.ncols)
		if (payload := cell_payload(sheet, row, col))
	]
	sections = section_lookup(day, sheet)
	for cell in cells:
		if section := sections.get(cell["a"]):
			cell["s"] = section

	datasets = []
	for name, spec in DATASETS.items():
		records = spec.trace(day, sheet)
		if not records:
			continue
		verify(name, records, day)
		datasets.append({
			"id": spec.id,
			"label": spec.label,
			"table": parse.DATASET_FILES[name],
			"note": spec.note,
			"key": spec.key,
			"fields": fields_of(name),
			"records": [
				{"label": record.label, "values": record.values, "cells": record.cells}
				for record in records
			],
		})

	mapped = {
		cell
		for entry in datasets
		for record in entry["records"]
		for cells in record["cells"].values()
		for cell in cells
	}
	return {
		"reportDate": day.isoformat(),
		"workbook": path.name,
		"sourceUrl": SOURCE_URL,
		"sheet": {"name": sheet.name, "rows": sheet.nrows, "columns": sheet.ncols},
		"cells": cells,
		"mappedCells": len(mapped),
		"datasets": datasets,
	}


def resolve_workbook(requested: str | None) -> tuple[date, Path]:
	workbooks = parse.available_workbooks(RAW_DIR)
	if not workbooks:
		raise SystemExit(
			f"No workbooks in {RAW_DIR.relative_to(ROOT)}. Run fetch.py before building this payload."
		)
	if requested is None:
		day = max(workbooks)
		return day, workbooks[day]
	day = parse.parse_date(requested)
	if day not in workbooks:
		raise SystemExit(f"No workbook for {day} in {RAW_DIR.relative_to(ROOT)}.")
	return day, workbooks[day]


def main(argv: list[str] | None = None) -> int:
	argument_parser = argparse.ArgumentParser(description=__doc__)
	argument_parser.add_argument("--date", help="report date to trace (defaults to the latest raw workbook)")
	arguments = argument_parser.parse_args(argv)

	day, path = resolve_workbook(arguments.date)
	print(f"Tracing {path.name} ({day})")
	payload = build(day, path)
	OUTPUT.parent.mkdir(parents=True, exist_ok=True)
	OUTPUT.write_text(
		json.dumps(payload, separators=(",", ":"), ensure_ascii=False, allow_nan=False),
		encoding="utf-8",
	)
	print(
		f"Wrote {OUTPUT.relative_to(ROOT)} "
		f"({OUTPUT.stat().st_size / 1024:.0f} KiB, {len(payload['cells'])} cells, "
		f"{payload['mappedCells']} mapped)"
	)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
