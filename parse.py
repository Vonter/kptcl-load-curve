#!/usr/bin/env python3
"""Parse KPTCL workbooks into clean datasets and source-rich debug Parquets."""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Iterable

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import xlrd
from xlrd.formula import colname

ROOT = Path(__file__).resolve().parent
MONTHS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")

DEBUG_DATASET_COLUMNS = {
    "load_curve": [
        "report_date", "observed_at", "report_hour", "grid_load_mw", "frequency_hz",
    ],
    "stations": [
        "report_date", "category", "station", "source_station", "installed_units",
        "installed_capacity_mw", "units_generating", "generation_at_state_max_mw",
        "generation_at_state_min_mw", "energy_generated_mu", "record_max_mw",
    ],
    "reservoirs": [
        "report_date", "observed_at", "reservoir", "energy_capacity_mu",
        "full_reservoir_level", "full_reservoir_level_unit", "capacity_mcft",
        "previous_year_level", "current_level",
        "previous_year_live_capacity_mcft", "current_live_capacity_mcft",
        "previous_year_equivalent_energy_mu", "current_equivalent_energy_mu",
        "previous_year_storage_percent", "current_storage_percent",
        "previous_year_inflow_cusecs", "current_inflow_cusecs",
        "previous_year_inflow_mu", "current_inflow_mu",
        "previous_year_discharge_cusecs", "current_discharge_cusecs",
        "previous_year_monthly_inflow_mcft", "current_monthly_inflow_mcft",
        "previous_year_monthly_inflow_mu", "current_monthly_inflow_mu",
        "previous_year_progressive_inflow_mcft", "current_progressive_inflow_mcft",
    ],
    "outages": [
        "report_date", "system", "outage_type", "asset", "details",
        "from_time", "to_time", "remarks",
    ],
    "daily_summary": [
        "report_date", "sheet", "category", "entity", "metric", "unit",
        "value", "source_label", "source_column",
    ],
    "sections": [
        "report_date", "sheet", "section", "source_range", "cell_count", "cells_json",
    ],
}
FINAL_DATASET_COLUMNS = {
    "load_curve": DEBUG_DATASET_COLUMNS["load_curve"],
    "stations": [
        column for column in DEBUG_DATASET_COLUMNS["stations"] if column != "source_station"
    ],
    "reservoirs": DEBUG_DATASET_COLUMNS["reservoirs"],
    "outages": DEBUG_DATASET_COLUMNS["outages"],
    "daily_summary": [
        column
        for column in DEBUG_DATASET_COLUMNS["daily_summary"]
        if column not in {"sheet", "source_label", "source_column"}
    ],
    "sections": ["report_date", "section_type", "rows"],
}
DATASET_COLUMNS = DEBUG_DATASET_COLUMNS
DATASET_FILES = {
    "load_curve": "kptcl.parquet",
    "stations": "kptcl-stations.parquet",
    "reservoirs": "kptcl-reservoirs.parquet",
    "outages": "kptcl-outages.parquet",
    "daily_summary": "kptcl-daily-summary.parquet",
    "sections": "kptcl-report-sections.parquet",
}
CSV_DATASET_FILES = {
    name: filename.replace(".parquet", ".csv.zip")
    for name, filename in DATASET_FILES.items()
    if name != "sections"
}


def _cell_list(value_type: pa.DataType) -> pa.ListType:
    return pa.list_(pa.struct([
        pa.field("column", pa.string(), nullable=False),
        pa.field("value", value_type, nullable=False),
    ]))


SECTION_TEXT_CELLS_TYPE = _cell_list(pa.string())
SECTION_NUMBER_CELLS_TYPE = _cell_list(pa.float64())
SECTION_BOOLEAN_CELLS_TYPE = _cell_list(pa.bool_())
SECTION_DATETIME_CELLS_TYPE = _cell_list(pa.timestamp("us"))
SECTION_ROWS_TYPE = pa.list_(pa.struct([
    pa.field("text", SECTION_TEXT_CELLS_TYPE, nullable=False),
    pa.field("number", SECTION_NUMBER_CELLS_TYPE, nullable=False),
    pa.field("boolean", SECTION_BOOLEAN_CELLS_TYPE, nullable=False),
    pa.field("datetime", SECTION_DATETIME_CELLS_TYPE, nullable=False),
]))
SECTION_FINAL_SCHEMA = pa.schema([
    pa.field("report_date", pa.timestamp("us")),
    pa.field("section_type", pa.string()),
    pa.field("rows", SECTION_ROWS_TYPE),
])

# Source labels vary in punctuation, casing, spelling, and abbreviation. Keep this
# mapping explicit so names can be reviewed and extended without changing parser
# mechanics. Unlisted names are retained after whitespace normalization.
STATION_NAME_MAP = {
    "ALMATTI": "Almatti",
    "AP 66 KV": "AP 66 kV",
    "AP 66 kV": "AP 66 kV",
    "B.T.P.S.": "BTPS",
    "BHADRA": "Bhadra",
    "Bidadi WE": "Bidadi WE",
    "Bidadi WTE": "Bidadi Waste-to-Energy",
    "Bundled Power": "Bundled Power",
    "Captive Plants": "Captive Plants",
    "CGS Adjustments+PX Exp": "CGS Adjustments + PX Export",
    "CGS Adjustments(stoa+LTA+IEX)": "CGS Adjustments (STOA + LTA + IEX)",
    "DVC": "DVC",
    "GERUSOPPA": "Gerusoppa",
    "GHATAPRABA": "Ghataprabha",
    "Global": "Global",
    "GRAND TOTAL": "Grand Total",
    "JINDAL": "Jindal",
    "Jurala": "Jurala",
    "KADRA": "Kadra",
    "KODASALLY": "Kodasalli",
    "L.D.P.H.": "LDPH",
    "M.D.P.H.": "MDPH",
    "M.G.H.E.": "MGHE",
    "Maharastra system": "Maharashtra System",
    "Mini Thermal(Conventional)": "Mini Thermal (Conventional)",
    "MSEDCL": "MSEDCL",
    "MUNIRABAD": "Munirabad",
    "N. P. H.": "NPH",
    "N.C.E Sources": "NCE Sources",
    "N.C.E Sources + Solar(10 MW)": "NCE Sources + Solar (10 MW)",
    "N.C.E Sources 1) Solar": "NCE - Solar",
    "N.C.E Sources 1) Solar(10 MW)": "NCE - Solar (10 MW)",
    "NET CGS IMPORT": "Net CGS Import",
    "NET CGS IMPORT ( ISGS +UI)": "Net CGS Import (ISGS + UI)",
    "NET CGS IMPORT( ISGS +UI+RAILWAYS)": "Net CGS Import (ISGS + UI + Railways)",
    "NET CGS IMPORT ( ISGS +UI+RAILWAYS+Bundled power)": "Net CGS Import (ISGS + UI + Railways + Bundled Power)",
    "NET CGS IMPORT( ISGS +UI+RAILWAYS+Bundled power)": "Net CGS Import (ISGS + UI + Railways + Bundled Power)",
    "R.T.P.S.": "RTPS",
    "Railways": "Railways",
    "RAYAL SEEMA": "Rayalaseema",
    "Shakti Policy": "Shakti Policy",
    "SHARAVATHY": "Sharavathi",
    "SHIMSHAPURA": "Shimshapura",
    "SIVASAMUDRA": "Sivasamudra",
    "SIVASAMUDRA & SHIMSHA": "Sivasamudra & Shimsha",
    "Small Thermal(Conventional)": "Small Thermal (Conventional)",
    "SOLAR(KPCL)": "Solar (KPCL)",
    "STOA+LTA+IEX": "STOA + LTA + IEX",
    "STOA/MTOA+IEX+URS+RTM": "STOA / MTOA / IEX / URS / RTM",
    "SUPA": "Supa",
    "TATA Elec. Co.": "Tata Electric Company",
    "TB Dam Share": "TB Dam Share",
    "TOTAL": "Total",
    "Total Energy from IPP'S": "Total Energy from IPPs",
    "Total NCE": "Total NCE",
    "Total NCE(PROVISIONAL)": "Total NCE (Provisional)",
    "UPCL": "UPCL",
    "VARAHI": "Varahi",
    "Y.D.G.S.": "YDGS",
    "Y.T.P.S.": "YTPS",
    "YCCP": "YCCP",
    "YTPS": "YTPS",
    "2) Captive & Co-Gen": "NCE - Captive & Cogeneration",
    "2) Co-Gen": "NCE - Cogeneration",
    "3) Wind": "NCE - Wind",
    "4) Mini Hydel": "NCE - Mini Hydel",
    "5) Bio mass": "NCE - Biomass",
}

SUMMARY_GENERATION_LABELS = {
    "ALMATTI", "B.T.P.S.", "BHADRA", "GERUSOPPA", "GHATAPRABA", "JURALA",
    "KADRA", "KODASALLY", "L.D.P.H.", "M.D.P.H.", "M.G.H.E.", "MUNIRABAD",
    "N. P. H.", "R.T.P.S.", "SHARAVATHY", "SHIMSHAPURA", "SIVASAMUDRA",
    "SIVASAMUDRA & SHIMSHA", "SOLAR", "SOLAR(KPCL)", "SUPA", "TB DAM SHARE",
    "VARAHI", "Y.D.G.S.", "Y.T.P.S.", "YCCP", "YTPS",
    "CONVENTIONAL", "NCE PROJECTS",
}


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("dates must use YYYY-MM-DD") from exc


def workbook_name(day: date) -> str:
    return f"D{day:%d}{MONTHS[day.month - 1]}{day:%Y}.xls"


def workbook_date(path: Path) -> date:
    match = re.fullmatch(r"D(\d{2})([A-Z]{3})(\d{4})\.xls", path.name, re.I)
    if not match:
        raise ValueError(f"Cannot infer report date from {path.name}")
    source_day, month, year = match.groups()
    return date(int(year), MONTHS.index(month.upper()) + 1, int(source_day))


def date_range(start: date, end: date) -> list[date]:
    if end < start:
        raise ValueError("--end must not be earlier than --start")
    return [start + timedelta(days=offset) for offset in range((end - start).days + 1)]


def _clean(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return re.sub(r"\s+", " ", str(value)).strip()


def _number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = _clean(value).replace(",", "")
    if not text or text in {"-", "`", ".", "!", "*"}:
        return None
    return float(text) if re.fullmatch(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", text) else None


@dataclass(slots=True)
class SheetView:
    sheet: xlrd.sheet.Sheet
    values: list[list[str]] = field(init=False)
    populated: list[tuple[int, int, str]] = field(init=False)

    def __post_init__(self) -> None:
        self.values = [
            [_clean(self.sheet.cell_value(row, col)) for col in range(self.sheet.ncols)]
            for row in range(self.sheet.nrows)
        ]
        self.populated = [
            (row, col, value.casefold())
            for row, values in enumerate(self.values)
            for col, value in enumerate(values)
            if value
        ]

    @property
    def nrows(self) -> int:
        return self.sheet.nrows

    @property
    def ncols(self) -> int:
        return self.sheet.ncols

    def text(self, row: int, col: int) -> str:
        return self.values[row][col]

    def __getattr__(self, name: str) -> object:
        return getattr(self.sheet, name)

    def find(self, needle: str, *, exact: bool = False) -> tuple[int, int] | None:
        folded = needle.casefold()
        return next(
            (
                (row, col)
                for row, col, value in self.populated
                if value == folded or (not exact and folded in value)
            ),
            None,
        )

    def row_text(self, row: int) -> str:
        return " ".join(self.values[row]).casefold()


def view(sheet: xlrd.sheet.Sheet | SheetView) -> SheetView:
    return sheet if isinstance(sheet, SheetView) else SheetView(sheet)


def parse_date_from_path(path: Path) -> date:
    return workbook_date(path)


def _station_number(value: object) -> float | None:
    """Parse station values while allowing footnoted forms such as ``(115)*``."""
    number = _number(value)
    if number is not None:
        return number
    text = _clean(value).replace(",", "")
    match = re.fullmatch(r"\(?\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+))\s*\)?\s*\**", text)
    return float(match.group(1)) if match else None


def normalize_station_name(source: str) -> str:
    return STATION_NAME_MAP.get(source, source)


def _frame(dataset: str, rows: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=DATASET_COLUMNS[dataset])
    if not frame.empty:
        frame["report_date"] = pd.to_datetime(frame["report_date"])
        for column in (name for name in frame if name.startswith("observed_at")):
            frame[column] = pd.to_datetime(frame[column])
    return frame


def _find(
    sheet: xlrd.sheet.Sheet | SheetView,
    needle: str,
    *,
    exact: bool = False,
) -> tuple[int, int] | None:
    return view(sheet).find(needle, exact=exact)


def _load_curve_anchor(sheet: xlrd.sheet.Sheet | SheetView) -> tuple[int, int] | None:
    sheet = view(sheet)
    for row in range(sheet.nrows):
        for col in range(sheet.ncols):
            if sheet.text(row, col).upper() != "TIME":
                continue
            nearby = " ".join(
                sheet.text(nearby_row, c).upper()
                for nearby_row in range(row, min(row + 2, sheet.nrows))
                for c in range(col, min(col + 4, sheet.ncols))
            )
            # A few source reports publish the full 0-24 load series without a
            # frequency column. The load curve is still useful and frequency is
            # correctly represented as null for those source-absent values.
            if "LOAD" in nearby:
                return row, col
    return None


def parse_load_curve(day: date, sheet: xlrd.sheet.Sheet | SheetView) -> list[dict]:
    sheet = view(sheet)
    anchor = _load_curve_anchor(sheet)
    if not anchor:
        return []
    header_row, time_col = anchor
    nearby_headers = {
        col: " ".join(
            _clean(sheet.cell_value(row, col)).upper()
            for row in range(header_row, min(header_row + 2, sheet.nrows))
        )
        for col in range(time_col, min(time_col + 4, sheet.ncols))
    }
    load_col = next((col for col, header in nearby_headers.items() if "LOAD" in header), time_col + 1)
    frequency_col = next((col for col, header in nearby_headers.items() if "FREQUENCY" in header), None)
    rows = []
    seen_hours: set[int] = set()
    for row in range(header_row + 1, min(sheet.nrows, header_row + 32)):
        raw_hour = _number(sheet.cell_value(row, time_col))
        if raw_hour is None or not raw_hour.is_integer():
            continue
        hour = int(raw_hour)
        if hour not in range(25) or hour in seen_hours:
            continue
        load = _number(sheet.cell_value(row, load_col)) if load_col < sheet.ncols else None
        frequency = _number(sheet.cell_value(row, frequency_col)) if frequency_col is not None else None
        if load is None and frequency is None:
            continue
        seen_hours.add(hour)
        rows.append({
            "report_date": day,
            "observed_at": datetime.combine(day, time()) + timedelta(hours=hour),
            "report_hour": hour,
            "grid_load_mw": load,
            "frequency_hz": frequency,
        })
    return rows


def parse_stations(day: date, sheet: xlrd.sheet.Sheet | SheetView) -> list[dict]:
    sheet = view(sheet)
    anchor = _find(sheet, "STATIONS", exact=True)
    if not anchor:
        return []
    header_row, station_col = anchor
    rows: list[dict] = []
    category = "generation and exchanges"
    if station_col > 0 and header_row > 0:
        preceding = _clean(sheet.cell_value(header_row - 1, station_col - 1))
        if preceding.endswith((":", ":-")):
            category = re.sub(r"^[A-Z]\.?\s*", "", preceding.rstrip(":- "), flags=re.I)
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
        station = _clean(sheet.cell_value(row, station_col))
        left = _clean(sheet.cell_value(row, station_col - 1)) if station_col > 0 else ""
        if not station and left.endswith((":", ":-")):
            category = re.sub(r"^[A-Z]\.?\s*", "", left.rstrip(":- "), flags=re.I)
            continue
        if not station and left.upper() in {"TOTAL", "GRAND TOTAL"}:
            station = left
        if not station:
            continue
        upper = station.upper()
        if upper.startswith(("PROJECTION", "ENERGY CONSUMED", "BALANCE AS", "RAINFALL")):
            break
        if upper.endswith((":", ":-")):
            category = station.rstrip(":- ")
            continue
        record = {
            "report_date": day,
            "category": category,
            "station": normalize_station_name(station),
            "source_station": station,
        }
        for offset, field in fields.items():
            if station_col + offset < sheet.ncols:
                record[field] = _station_number(sheet.cell_value(row, station_col + offset))
        if any(record.get(field) is not None for field in fields.values()):
            rows.append(record)
        if upper == "GRAND TOTAL":
            break
    return rows


def _reservoir_metric(label: str) -> str | None:
    normalized = re.sub(r"[^a-z0-9%]+", " ", label.casefold()).strip()
    if normalized == "level":
        return "level"
    if normalized.startswith("live capty"):
        return "live_capacity_mcft"
    if normalized.startswith("eq energy"):
        return "equivalent_energy_mu"
    if normalized.startswith("% storage"):
        return "storage_percent"
    if normalized.startswith("inflow in cusec"):
        return "inflow_cusecs"
    if normalized.startswith("inflow in mu"):
        return "inflow_mu"
    if normalized.startswith("discharge cusec"):
        return "discharge_cusecs"
    if normalized.startswith("inflow during the month in mcft"):
        return "monthly_inflow_mcft"
    if normalized.startswith("inflow during the month in mu"):
        return "monthly_inflow_mu"
    if normalized.startswith("i f prog"):
        return "progressive_inflow_mcft"
    return None


def _reservoir_observed_at(
    day: date,
    sheet: xlrd.sheet.Sheet | SheetView,
) -> datetime | None:
    sheet = view(sheet)
    anchor = next(
        (
            (row, col)
            for row in range(sheet.nrows)
            for col in range(sheet.ncols)
            if "reservoir" in _clean(sheet.cell_value(row, col)).casefold()
            and "details" in _clean(sheet.cell_value(row, col)).casefold()
            and "hrs" in _clean(sheet.cell_value(row, col)).casefold()
        ),
        None,
    )
    if not anchor:
        return None
    row, col = anchor
    text = _clean(sheet.cell_value(row, col))
    clock = re.search(r"(\d{1,2})(\d{2})\s*HRS", text, re.I)
    if not clock:
        return None
    try:
        after_clock = text[clock.end():]
        printed = re.search(
            r"(?:ON\s*)?(\d{1,2})\s*(?:ST|ND|RD|TH|D)?\s*([A-Z]+)[- ]+(\d{2,4})",
            after_clock,
            re.I,
        )
        if printed:
            month = next(index for index, name in enumerate(MONTHS, 1) if name in printed.group(2).upper())
            year = int(printed.group(3))
            year += 2000 if year < 100 else 0
            observed_day = date(year, month, int(printed.group(1)))
        else:
            day_text = " ".join(_clean(sheet.cell_value(row, c)) for c in range(col + 1, min(col + 4, sheet.ncols)))
            printed_day = re.search(r"(\d{1,2})\s*(?:ST|ND|RD|TH|D)?", day_text, re.I)
            date_cell = next(
                (
                    sheet.cell(row, c).value for c in range(col + 1, min(col + 8, sheet.ncols))
                    if sheet.cell_type(row, c) == xlrd.XL_CELL_DATE
                ),
                None,
            )
            if not printed_day or date_cell is None:
                return None
            month_year = xlrd.xldate_as_datetime(date_cell, sheet.book.datemode)
            try:
                observed_day = date(month_year.year, month_year.month, int(printed_day.group(1)))
            except ValueError:
                # A small set of month-end reports prints impossible ordinals
                # such as 31 September or 29 February 2014. Their observation
                # is the next morning, consistent with the report sequence.
                observed_day = day + timedelta(days=1)
        return datetime.combine(observed_day, time(int(clock.group(1)), int(clock.group(2))))
    except (ValueError, StopIteration):
        return None


def parse_reservoirs(day: date, sheet: xlrd.sheet.Sheet | SheetView) -> list[dict]:
    sheet = view(sheet)
    anchor = _find(sheet, "RESERVOIR", exact=True)
    if not anchor:
        return []
    header_row, label_col = anchor
    installed = _find(sheet, "INSTALLED CAPACITY")
    end_row = installed[0] if installed else min(header_row + 17, sheet.nrows)
    names: list[tuple[int, str, float | None]] = []
    canonical_names = {"L.MAKKI": "Linganamakki", "L MAKKI": "Linganamakki", "SUPA": "Supa", "MANI": "Mani"}
    for col in range(label_col + 1, sheet.ncols):
        text = _clean(sheet.cell_value(header_row, col))
        upper = text.upper()
        key = next((name for name in canonical_names if name in upper), None)
        if not key:
            continue
        capacity_match = re.search(r"\(([\d,.]+)\s*MU\)", text, re.I)
        energy_capacity = float(capacity_match.group(1).replace(",", "")) if capacity_match else None
        names.append((col, canonical_names[key], energy_capacity))
    observed_at = _reservoir_observed_at(day, sheet)
    records = [{
        "report_date": day,
        "observed_at": observed_at,
        "reservoir": name,
        "energy_capacity_mu": energy_capacity,
    } for _, name, energy_capacity in names]
    for index, (start_col, _name, _energy) in enumerate(names):
        stop_col = names[index + 1][0] if index + 1 < len(names) else min(start_col + 8, sheet.ncols)
        record = records[index]
        for row in range(header_row + 1, end_row):
            label = _clean(sheet.cell_value(row, label_col))
            upper = label.upper()
            if upper.startswith("FULL RESERVOIR LEVEL"):
                text = _clean(sheet.cell_value(row, start_col))
                value = re.search(r"[-+]?[\d,.]+", text)
                record["full_reservoir_level"] = float(value.group().replace(",", "")) if value else None
                unit = re.search(r"\b(FT|FEET|MTRS?|METERS?)\b", text, re.I)
                record["full_reservoir_level_unit"] = unit.group().lower() if unit else None
                continue
            if upper.startswith("CAPACITY IN MCFT"):
                text = _clean(sheet.cell_value(row, start_col))
                value = re.match(r"[\d,.]+", text)
                record["capacity_mcft"] = float(value.group().replace(",", "")) if value else None
                continue
            metric = _reservoir_metric(label)
            if not metric:
                continue
            values = [
                value
                for col in range(start_col, stop_col)
                if (value := _number(sheet.cell_value(row, col))) is not None
            ]
            if values:
                record[f"previous_year_{metric}"] = values[0]
                if len(values) > 1:
                    record[f"current_{metric}"] = values[-1]
    return records


def _generator_asset(details: str) -> str:
    match = re.search(r"\b(?:O\s*/?\s*O|TRIPPED|OUT)\b", details, re.I)
    prefix = details[:match.start()] if match else details.split("-", 1)[0]
    return prefix.rstrip(" :-")


def _generator_outages(day: date, sheet: SheetView, system: str, heading: str, stop_headings: tuple[str, ...]) -> list[dict]:
    anchor = _find(sheet, heading)
    if not anchor:
        return []
    heading_row, _ = anchor
    header_row = heading_row + 1
    type_columns = []
    for col in range(sheet.ncols):
        header = _clean(sheet.cell_value(header_row, col)).casefold()
        if "planned outage" in header:
            type_columns.append((col, "planned"))
        elif "forced outage" in header:
            type_columns.append((col, "forced"))
    rows = []
    previous_by_column: dict[int, dict] = {}
    for row in range(header_row + 1, sheet.nrows):
        row_text = sheet.row_text(row)
        if any(stop.casefold() in row_text for stop in stop_headings):
            break
        for col, outage_type in type_columns:
            details = _clean(sheet.cell_value(row, col))
            if not details or not re.search(r"[A-Za-z]", details):
                continue
            if re.match(r"^(?:[-&]|AND\b|SYN(?:C)?\b)", details, re.I) and col in previous_by_column:
                previous_by_column[col]["details"] += " " + details.lstrip(" -&")
                continue
            record = {
                "report_date": day,
                "system": system,
                "outage_type": outage_type,
                "asset": _generator_asset(details) or "Unspecified generator",
                "details": details,
            }
            rows.append(record)
            previous_by_column[col] = record
    return rows


def _line_outages(day: date, sheet: SheetView, heading: str, outage_type: str, stop_headings: tuple[str, ...]) -> list[dict]:
    anchor = _find(sheet, heading)
    if not anchor:
        return []
    heading_row, heading_col = anchor
    local_header_row = heading_row + 1
    has_local_header = any(
        _clean(sheet.cell_value(local_header_row, col)).casefold() == "from"
        for col in range(sheet.ncols)
    )
    shared_header = _find(sheet, "Name of the line")
    header_row, asset_col = (
        (local_header_row, heading_col)
        if has_local_header or not shared_header
        else shared_header
    )
    first_data_row = local_header_row + 1 if has_local_header else heading_row + 1
    columns = {"asset": asset_col}
    for col in range(asset_col, sheet.ncols):
        header = _clean(sheet.cell_value(header_row, col)).casefold()
        if header == "from":
            columns["from_time"] = col
        elif header == "to":
            columns["to_time"] = col
        elif header == "details":
            columns["details"] = col
        elif header == "remarks":
            columns["remarks"] = col
    rows = []
    for row in range(first_data_row, sheet.nrows):
        row_text = sheet.row_text(row)
        asset = _clean(sheet.cell_value(row, columns["asset"]))
        # Dashboard sections can begin in columns to the left while a valid line
        # record continues on the same row. Stop only once a stop heading occurs
        # on a row that has no line asset.
        if not asset and any(stop.casefold() in row_text for stop in stop_headings):
            break
        if not asset:
            continue
        record = {"report_date": day, "system": "major_line", "outage_type": outage_type, "asset": asset}
        for field in ("details", "from_time", "to_time", "remarks"):
            if field in columns:
                record[field] = _clean(sheet.cell_value(row, columns[field])) or None
        classification = " ".join(_clean(record.get(field)) for field in ("details", "remarks"))
        if outage_type == "line_clear_or_outage" and re.search(
            r"\b(?:O\s*/?\s*O\s+ON\s+)?(?:OV|PR)\b|OVER\s*VOLT|POWER\s*REG",
            classification,
            re.I,
        ):
            record["outage_type"] = "over_voltage_or_power_regulation"
        rows.append(record)
    return rows


def parse_outages(day: date, sheet: xlrd.sheet.Sheet | SheetView) -> list[dict]:
    sheet = view(sheet)
    rows = _generator_outages(day, sheet, "central_generator", "Central Generator Outages", ("State Generator Outages",))
    rows += _generator_outages(day, sheet, "state_generator", "State Generator Outages", ("Unscheduled Load Curtailment", "Major Lines (Over Voltage"))
    rows += _line_outages(day, sheet, "Major Lines (Line Clears & Outages)", "line_clear_or_outage", ("State Generator Outages",))
    rows += _line_outages(day, sheet, "Major Lines (Over Voltage & Power Regulation)", "over_voltage_or_power_regulation", ("Rainfall", "Projection"))
    return rows


def _daily_summary_header(sheet: xlrd.sheet.Sheet | SheetView) -> int | None:
    sheet = view(sheet)
    """Locate the transposed one-row daily summary used in auxiliary sheets."""
    markers = {"state peak", "state min", "karnataka consumption"}
    for row in range(sheet.nrows - 1):
        labels = [_clean(sheet.cell_value(row, col)).casefold() for col in range(sheet.ncols)]
        if not markers.intersection(labels):
            continue
        paired = sum(
            bool(labels[col]) and _number(sheet.cell_value(row + 1, col)) is not None
            for col in range(sheet.ncols)
        )
        if paired >= 10:
            return row
    return None


def _summary_identity(source_label: str) -> tuple[str, str, str, str | None]:
    label = _clean(source_label)
    upper = re.sub(r"\s+", " ", label.upper())
    station_key = next((key for key in STATION_NAME_MAP if key.upper() == upper), None)
    if upper in SUMMARY_GENERATION_LABELS:
        return "generation", normalize_station_name(station_key or label), "energy_generated", "MU"
    grid_metrics = {
        "STATE PEAK": ("Karnataka grid", "maximum_demand", "MW"),
        "STATE MIN": ("Karnataka grid", "minimum_demand", "MW"),
        "MAX FREQ": ("Karnataka grid", "maximum_frequency", "Hz"),
        "MIN FREQ": ("Karnataka grid", "minimum_frequency", "Hz"),
        "KARNATAKA CONSUMPTION": ("Karnataka grid", "energy_consumed", "MU"),
        "DATE": ("Report", "day_of_month", None),
    }
    if upper in grid_metrics:
        entity, metric, unit = grid_metrics[upper]
        return "grid", entity, metric, unit
    reservoir_match = re.match(r"(SGS|SGA|LMK|SUPA|MANI)\s+(.+)", upper)
    if reservoir_match:
        reservoir = {
            "SGS": "Linganamakki",
            "SGA": "Linganamakki",
            "LMK": "Linganamakki",
            "SUPA": "Supa",
            "MANI": "Mani",
        }[reservoir_match.group(1)]
        suffix = reservoir_match.group(2)
        if "LEVEL" in suffix:
            return "reservoir", reservoir, "level", None
        if "EQV" in suffix or suffix == "MU":
            return "reservoir", reservoir, "equivalent_energy", "MU"
        if "INFLOW" in suffix or "IN FLOW" in suffix:
            return "reservoir", reservoir, "inflow", "cusecs"
        if "DISCH" in suffix:
            return "reservoir", reservoir, "discharge", "cusecs"
    metric = re.sub(r"[^a-z0-9]+", "_", label.casefold()).strip("_")
    return "exchange", label, metric or "value", "MU"


def parse_daily_summary(day: date, sheet: xlrd.sheet.Sheet | SheetView) -> list[dict]:
    sheet = view(sheet)
    header_row = _daily_summary_header(sheet)
    if header_row is None:
        return []
    rows = []
    for col in range(sheet.ncols):
        source_label = _clean(sheet.cell_value(header_row, col))
        value = _number(sheet.cell_value(header_row + 1, col))
        if not source_label or value is None:
            continue
        category, entity, metric, unit = _summary_identity(source_label)
        rows.append({
            "report_date": day,
            "sheet": sheet.name,
            "category": category,
            "entity": entity,
            "metric": metric,
            "unit": unit,
            "value": value,
            "source_label": source_label,
            "source_column": colname(col),
        })
    return rows


def _rect(top: int, bottom: int, left: int, right: int) -> set[tuple[int, int]]:
    """Return a zero-based, half-open cell rectangle."""
    return {(row, col) for row in range(max(0, top), max(0, bottom)) for col in range(max(0, left), max(0, right))}


def _excel_range(coords: set[tuple[int, int]]) -> str:
    if not coords:
        return ""
    rows = [row for row, _ in coords]
    cols = [col for _, col in coords]
    return f"{colname(min(cols))}{min(rows) + 1}:{colname(max(cols))}{max(rows) + 1}"


def _json_cell(sheet: xlrd.sheet.Sheet | SheetView, row: int, col: int) -> dict:
    cell = sheet.cell(row, col)
    kinds = {
        xlrd.XL_CELL_TEXT: "text",
        xlrd.XL_CELL_NUMBER: "number",
        xlrd.XL_CELL_DATE: "date",
        xlrd.XL_CELL_BOOLEAN: "boolean",
        xlrd.XL_CELL_ERROR: "error",
    }
    kind = kinds.get(cell.ctype, "unknown")
    value: object = cell.value
    if kind == "number":
        value = int(value) if isinstance(value, float) and value.is_integer() else value
    elif kind == "boolean":
        value = bool(value)
    elif kind == "date":
        try:
            value = xlrd.xldate_as_datetime(value, sheet.book.datemode).isoformat()
        except (TypeError, ValueError, xlrd.XLDateError):
            value = _clean(value)
    elif kind == "error":
        value = xlrd.error_text_from_code.get(value, f"error-{value}")
    return {
        "cell": f"{colname(col)}{row + 1}",
        "row": row + 1,
        "column": colname(col),
        "type": kind,
        "value": value,
    }


def parse_sections(day: date, sheet: xlrd.sheet.Sheet | SheetView) -> list[dict]:
    """Preserve source section layout, including content not in semantic tables.

    Each section is one Parquet row containing typed, addressed cells as JSON.
    Unclaimed populated cells are retained in an ``unclassified`` fallback, so a
    new workbook layout cannot silently lose source content.
    """
    sheet = view(sheet)
    records: list[dict] = []
    claimed: set[tuple[int, int]] = set()
    indexed_cells = sheet.populated

    def find(needle: str, *, exact: bool = False) -> tuple[int, int] | None:
        folded = needle.casefold()
        return next(
            (
                (row, col) for row, col, value in indexed_cells
                if ((value == folded) if exact else (folded in value))
            ),
            None,
        )

    def add(name: str, coords: set[tuple[int, int]], source_range: str | None = None) -> None:
        present = {
            (row, col) for row, col in coords
            if row < sheet.nrows and col < sheet.ncols and sheet.text(row, col)
        }
        if not present:
            return
        claimed.update(present)
        cells = [_json_cell(sheet, row, col) for row, col in sorted(present)]
        records.append({
            "report_date": day,
            "sheet": sheet.name,
            "section": name,
            "source_range": source_range or _excel_range(coords),
            "cell_count": len(cells),
            "cells_json": json.dumps(cells, ensure_ascii=False, separators=(",", ":"), allow_nan=False),
        })

    reservoir = find("RESERVOIR", exact=True)
    installed = find("INSTALLED CAPACITY")
    if reservoir:
        end = installed[0] if installed else min(reservoir[0] + 17, sheet.nrows)
        add("reservoir_details", _rect(max(0, reservoir[0] - 2), end, reservoir[1], min(reservoir[1] + 19, sheet.ncols)))

    load = _load_curve_anchor(sheet)
    if load:
        load_rows = {load[0]}
        for row in range(load[0] + 1, min(load[0] + 32, sheet.nrows)):
            hour = _number(sheet.cell_value(row, load[1]))
            if hour is not None and hour.is_integer() and int(hour) in range(25):
                load_rows.add(row)
        add("hourly_load_curve", {(row, col) for row in load_rows for col in range(load[1], min(load[1] + 3, sheet.ncols))})

    stations = find("STATIONS", exact=True)
    if stations:
        grand_total = find("GRAND TOTAL", exact=True)
        end = grand_total[0] + 1 if grand_total and grand_total[0] > stations[0] else min(stations[0] + 50, sheet.nrows)
        add("stations", _rect(max(0, stations[0] - 1), end, stations[1], min(stations[1] + 12, sheet.ncols)))

    tattihalla = find("Tattihalla")
    if tattihalla:
        add("minor_reservoir_flows", _rect(tattihalla[0] - 1, tattihalla[0] + 2, tattihalla[1], min(tattihalla[1] + 16, sheet.ncols)))

    availability = find("TOTAL AVAILABILITY FROM 3 MAJOR RESERVOIRS")
    if availability:
        add("major_reservoir_availability", _rect(availability[0] - 1, availability[0] + 2, availability[1], min(availability[1] + 18, sheet.ncols)))

    hydro = find("TOTAL HYDRO GENERATION")
    progressive = find("PROGRESSIVE STATE CONSUMPTION")
    cgs = find("SCHEDULES OF CENTRAL GENERATING STATIONS")
    if hydro:
        summary_start = hydro[0] + 4
        add("hydro_generation", _rect(hydro[0], min(summary_start, sheet.nrows), hydro[1], min(hydro[1] + 18, sheet.ncols)))
        summary_end = progressive[0] if progressive and progressive[0] > summary_start else min(summary_start + 3, sheet.nrows)
        add("generation_averages", _rect(summary_start, summary_end, hydro[1], min(hydro[1] + 18, sheet.ncols)))
    if progressive:
        end = cgs[0] if cgs and cgs[0] > progressive[0] else min(progressive[0] + 4, sheet.nrows)
        add("progressive_state_consumption", _rect(progressive[0], end, progressive[1], min(progressive[1] + 18, sheet.ncols)))

    central = find("Central Generator Outages")
    state = find("State Generator Outages")
    if cgs:
        end = central[0] if central and central[0] > cgs[0] else min(cgs[0] + 4, sheet.nrows)
        add("central_generation_schedule", _rect(cgs[0], end, cgs[1], min(cgs[1] + 19, sheet.ncols)))
    if central:
        end = state[0] if state and state[0] > central[0] else min(central[0] + 15, sheet.nrows)
        add("central_generator_outages", _rect(central[0], end, central[1], min(central[1] + 9, sheet.ncols)))

    line_clear = find("Major Lines (Line Clears & Outages)")
    if line_clear:
        end = state[0] if state and state[0] > line_clear[0] else min(line_clear[0] + 15, sheet.nrows)
        add("major_line_clears_and_outages", _rect(line_clear[0], end, line_clear[1], min(line_clear[1] + 10, sheet.ncols)))

    unscheduled = find("Unscheduled Load Curtailment")
    over_voltage = find("Major Lines (Over Voltage")
    if state:
        candidates = [pos[0] for pos in (unscheduled, over_voltage) if pos and pos[0] > state[0]]
        end = min(candidates) if candidates else min(state[0] + 10, sheet.nrows)
        add("state_generator_outages", _rect(state[0], end, state[1], min(state[1] + 9, sheet.ncols)))
    if unscheduled:
        add("unscheduled_load_curtailment", _rect(unscheduled[0], unscheduled[0] + 1, unscheduled[1], min(unscheduled[1] + 9, sheet.ncols)))
    if over_voltage:
        end = over_voltage[0] + 1
        while end < sheet.nrows and _clean(sheet.cell_value(end, over_voltage[1])):
            end += 1
        add("major_line_voltage_regulation", _rect(over_voltage[0], end, over_voltage[1], min(over_voltage[1] + 10, sheet.ncols)))

    rainfall = find("Rainfall")
    if rainfall:
        rain_cells = {(rainfall[0], rainfall[1])}
        for row in range(rainfall[0], min(rainfall[0] + 5, sheet.nrows)):
            for col in range(sheet.ncols - 2):
                if (
                    sheet.cell_type(row, col) == xlrd.XL_CELL_TEXT
                    and _clean(sheet.cell_value(row, col))
                    and _number(sheet.cell_value(row, col + 1)) is not None
                    and _number(sheet.cell_value(row, col + 2)) is not None
                ):
                    rain_cells.update({(row, col), (row, col + 1), (row, col + 2)})
        add("rainfall", rain_cells)

    annual_projection = find("PROJECTION & ACTUALS FOR FY")
    monthly_projection = find("PROJECTION AND ACTUALS FOR")
    footnote = find("Installed Capacity of Railways")
    if annual_projection:
        end = monthly_projection[0] if monthly_projection and monthly_projection[0] > annual_projection[0] else min(annual_projection[0] + 5, sheet.nrows)
        add("annual_projection_and_actuals", _rect(annual_projection[0], end, annual_projection[1], min(annual_projection[1] + 11, sheet.ncols)))
    if monthly_projection:
        end = footnote[0] if footnote and footnote[0] > monthly_projection[0] else min(monthly_projection[0] + 7, sheet.nrows)
        add("monthly_projection_and_actuals", _rect(monthly_projection[0], end, monthly_projection[1], min(monthly_projection[1] + 11, sheet.ncols)))

    dam_levels = find("Dam levels(as on date)")
    if dam_levels:
        add("dam_levels", _rect(dam_levels[0] - 1, dam_levels[0] + 2, dam_levels[1], min(dam_levels[1] + 7, sheet.ncols)))

    exports = find("Jindal to outside")
    purchases = find("Power Purchased in MU")
    if exports:
        end = purchases[0] if purchases and purchases[0] > exports[0] else min(exports[0] + 2, sheet.nrows)
        add("energy_exports", _rect(exports[0], end, exports[1], min(exports[1] + 13, sheet.ncols)))
    if purchases:
        add("energy_purchases", _rect(purchases[0], min(purchases[0] + 6, sheet.nrows), purchases[1], min(purchases[1] + 13, sheet.ncols)))

    previous = find("Prev year's")
    if previous:
        populated_rows = [
            row for row in range(previous[0], sheet.nrows)
            if any(_clean(sheet.cell_value(row, col)) for col in range(previous[1], min(previous[1] + 2, sheet.ncols)))
        ]
        if populated_rows:
            add("previous_year_reference", _rect(previous[0], max(populated_rows) + 1, previous[1], min(previous[1] + 2, sheet.ncols)))

    if footnote:
        add("footnotes_and_signoff", _rect(footnote[0], footnote[0] + 1, footnote[1], min(footnote[1] + 31, sheet.ncols)))

    summary_header = _daily_summary_header(sheet)
    if summary_header is not None:
        add(
            "daily_summary",
            _rect(summary_header, min(summary_header + 2, sheet.nrows), 0, sheet.ncols),
        )

    historical_import = find("ENERGY IMPORT FROM IEX")
    if historical_import:
        add("historical_energy_import_reference", _rect(0, sheet.nrows, 0, sheet.ncols))

    form_d = find("FORM-D")
    if form_d:
        add("embedded_form_d_schedule", _rect(0, sheet.nrows, 0, sheet.ncols))

    remaining = {
        (row, col)
        for row in range(sheet.nrows)
        for col in range(sheet.ncols)
        if sheet.text(row, col) and (row, col) not in claimed
    }
    add("unclassified", remaining, _excel_range(remaining))
    return records


def parse_workbook(path: Path, report_date: date | None = None) -> dict[str, pd.DataFrame]:
    """Parse one workbook into semantic tables and source-section snapshots."""
    report_date = report_date or parse_date_from_path(path)
    book = xlrd.open_workbook(path)
    rows: dict[str, list[dict]] = {name: [] for name in DATASET_COLUMNS}
    load_candidates: list[list[dict]] = []
    for source_sheet in book.sheets():
        sheet = view(source_sheet)
        load_curve = parse_load_curve(report_date, sheet)
        if load_curve:
            load_candidates.append(load_curve)
        rows["stations"].extend(parse_stations(report_date, sheet))
        rows["reservoirs"].extend(parse_reservoirs(report_date, sheet))
        rows["outages"].extend(parse_outages(report_date, sheet))
        rows["daily_summary"].extend(parse_daily_summary(report_date, sheet))
        rows["sections"].extend(parse_sections(report_date, sheet))
    if load_candidates:
        # Some workbooks contain both a published curve and an experimental
        # duplicate sheet. Prefer the most complete curve with the most
        # plausible frequency observations, retaining one row per report hour.
        best_curve = max(
            load_candidates,
            key=lambda candidate: (
                sum(40 <= record["frequency_hz"] <= 60 for record in candidate if record["frequency_hz"] is not None),
                len(candidate),
                sum(record["frequency_hz"] is not None for record in candidate),
            ),
        )
        rows["load_curve"].extend(best_curve)
    return {name: _frame(name, values) for name, values in rows.items()}


def _section_rows(payload: str) -> list[dict]:
    rows: list[dict] = []
    source_row: int | None = None
    target: dict[str, list[dict]] | None = None
    for cell in json.loads(payload):
        if int(cell["row"]) != source_row:
            source_row = int(cell["row"])
            target = {"text": [], "number": [], "boolean": [], "datetime": []}
            rows.append(target)
        item = {"column": str(cell["column"]), "value": cell["value"]}
        match cell["type"]:
            case "number":
                item["value"] = float(item["value"])
                target["number"].append(item)
            case "boolean":
                item["value"] = bool(item["value"])
                target["boolean"].append(item)
            case "date":
                item["value"] = pd.Timestamp(item["value"]).to_pydatetime()
                target["datetime"].append(item)
            case _:
                item["value"] = _clean(item["value"])
                target["text"].append(item)
    return rows


def final_dataset(dataset: str, frame: pd.DataFrame) -> pd.DataFrame:
    if dataset != "sections":
        return frame.loc[:, FINAL_DATASET_COLUMNS[dataset]].copy()
    final = frame.loc[:, ["report_date", "section"]].rename(
        columns={"section": "section_type"}
    )
    final["rows"] = frame["cells_json"].map(_section_rows)
    return final.loc[:, FINAL_DATASET_COLUMNS[dataset]]


def _merge_dataset(
    path: Path,
    frames: Iterable[pd.DataFrame],
    dates: set[pd.Timestamp],
    columns: list[str],
    replace: bool,
    seed_path: Path | None = None,
) -> pd.DataFrame:
    frames = list(frames)
    incoming = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=columns)
    existing = pd.DataFrame(columns=columns)
    existing_path = path if path.exists() else seed_path
    if existing_path is not None and existing_path.exists() and not replace:
        candidate = pd.read_parquet(existing_path)
        if list(candidate.columns) != columns:
            raise ValueError(f"incompatible debug schema in {existing_path}")
        existing = candidate.loc[~pd.to_datetime(candidate["report_date"]).isin(dates)]
    combined = pd.concat([existing, incoming], ignore_index=True)[columns]
    if not combined.empty:
        sort_columns = [
            column
            for column in (
                "report_date", "observed_at", "station", "reservoir", "system",
                "asset", "sheet", "category", "entity", "metric", "section",
            )
            if column in combined
        ]
        combined = (
            combined.drop_duplicates()
            .sort_values(
                sort_columns,
                ascending=[False] + [True] * (len(sort_columns) - 1),
                na_position="last",
            )
            .reset_index(drop=True)
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(path, index=False, compression="zstd")
    return combined


def _write_csv_zip(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    member = path.name.removesuffix(".zip")
    info = zipfile.ZipInfo(member, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        with archive.open(info, "w") as raw, io.TextIOWrapper(
            raw, encoding="utf-8", newline=""
        ) as stream:
            frame.to_csv(stream, index=False, lineterminator="\n")


def _write_final_dataset(dataset: str, frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if dataset != "sections":
        final = final_dataset(dataset, frame)
        final.to_parquet(path, index=False, compression="zstd")
        _write_csv_zip(final, path.with_suffix(".csv.zip"))
        return
    with pq.ParquetWriter(path, SECTION_FINAL_SCHEMA, compression="zstd") as writer:
        for start in range(0, len(frame), 512):
            batch = frame.iloc[start : start + 512]
            writer.write_table(pa.Table.from_arrays(
                [
                    pa.array(batch["report_date"], type=pa.timestamp("us")),
                    pa.array(batch["section"], type=pa.string()),
                    pa.array(batch["cells_json"].map(_section_rows), type=SECTION_ROWS_TYPE),
                ],
                schema=SECTION_FINAL_SCHEMA,
            ))


def save_parquets(
    parsed: Iterable[dict[str, pd.DataFrame]],
    report_dates: Iterable[date],
    data_dir: Path,
    replace: bool = False,
    debug_dir: Path = ROOT / "debug",
) -> dict[str, int]:
    if data_dir.resolve() == debug_dir.resolve():
        raise ValueError("--data-dir and --debug-dir must be different directories")
    parsed = list(parsed)
    dates = {pd.Timestamp(day) for day in report_dates}
    if not replace:
        for name, columns in DEBUG_DATASET_COLUMNS.items():
            debug_path = debug_dir / DATASET_FILES[name]
            data_path = data_dir / DATASET_FILES[name]
            if (
                not debug_path.exists()
                and data_path.exists()
                and pq.read_schema(data_path).names != columns
            ):
                raise ValueError(
                    f"cannot recreate missing {debug_path.name} from clean dataset; use --rebuild"
                )
    counts = {}
    for name, columns in DEBUG_DATASET_COLUMNS.items():
        debug_path = debug_dir / DATASET_FILES[name]
        data_path = data_dir / DATASET_FILES[name]
        seed_path = data_path if not debug_path.exists() and data_path.exists() and not replace else None
        debug_frame = _merge_dataset(
            debug_path,
            (item[name] for item in parsed),
            dates,
            columns,
            replace,
            seed_path,
        )
        _write_final_dataset(name, debug_frame, data_path)
        counts[name] = len(debug_frame)
    return counts


def latest_report_date(data_dir: Path) -> date | None:
    values = represented_report_dates(data_dir)
    return values[-1] if values else None


def represented_report_dates(data_dir: Path) -> list[date]:
    # Sections exist for every processed workbook, including rare source files
    # that genuinely omit the hourly curve. Fall back to the legacy load file
    # for repositories created before the section dataset was introduced.
    path = data_dir / DATASET_FILES["sections"]
    if not path.exists():
        path = data_dir / DATASET_FILES["load_curve"]
    if not path.exists():
        return []
    values = pd.read_parquet(path, columns=["report_date"])["report_date"]
    return sorted(pd.to_datetime(values).dt.date.unique())


def available_workbooks(raw_dir: Path) -> dict[date, Path]:
    return {parse_date_from_path(path): path for path in sorted(raw_dir.glob("D*.xls"))}


def requested_workbooks(args: argparse.Namespace) -> list[tuple[date, Path]]:
    if (args.rebuild or args.reparse) and (args.dates or args.start or args.end):
        raise ValueError("--rebuild and --reparse cannot be combined with dates, --start, or --end")
    if args.dates and (args.start or args.end):
        raise ValueError("dates cannot be combined with --start or --end")
    available = available_workbooks(args.raw_dir)
    if args.rebuild:
        days = sorted(available)
    elif args.reparse:
        days = represented_report_dates(args.data_dir)
    elif args.dates:
        days = sorted(set(args.dates))
    elif args.start or args.end:
        days = date_range(args.start or args.end, args.end or args.start)
    else:
        latest = latest_report_date(args.data_dir)
        days = [day for day in sorted(available) if latest is None or day > latest]
    return [(day, available.get(day, args.raw_dir / workbook_name(day))) for day in days]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dates", nargs="*", type=parse_date, metavar="YYYY-MM-DD")
    parser.add_argument("--start", type=parse_date, help="first date in an inclusive range")
    parser.add_argument("--end", type=parse_date, help="last date in an inclusive range")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--rebuild", action="store_true", help="parse every raw workbook and replace all datasets")
    mode.add_argument(
        "--reparse",
        action="store_true",
        help="regenerate every processed report date using the current parser",
    )
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "raw", help="workbook directory (default: raw)")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data", help="dataset directory (default: data)")
    parser.add_argument(
        "--debug-dir",
        type=Path,
        default=ROOT / "debug",
        help="source-rich Parquet directory (default: debug)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        workbooks = requested_workbooks(args)
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    failures = 0
    parsed_workbooks = []
    parsed_dates = []
    for day, path in workbooks:
        try:
            if not path.exists():
                raise FileNotFoundError(path)
            datasets = parse_workbook(path, day)
            if datasets["sections"].empty:
                raise ValueError("no populated source sections found")
            parsed_workbooks.append(datasets)
            parsed_dates.append(day)
            summary = ", ".join(f"{name}={len(frame)}" for name, frame in datasets.items())
            if datasets["load_curve"].empty:
                summary += "; source contains no hourly load curve"
            print(f"{day}: parsed {path.name}; {summary}")
        except (OSError, ValueError, xlrd.XLRDError) as exc:
            failures += 1
            print(f"ERROR {day}: {exc}", file=sys.stderr)
    if failures and (args.rebuild or args.reparse):
        print("Full regeneration aborted; existing Parquet files were not modified.", file=sys.stderr)
        return 1
    if parsed_workbooks:
        try:
            counts = save_parquets(
                parsed_workbooks,
                parsed_dates,
                args.data_dir,
                replace=args.rebuild,
                debug_dir=args.debug_dir,
            )
        except (OSError, ValueError, KeyError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        summary = ", ".join(
            f"{count} rows to {DATASET_FILES[name]}" for name, count in counts.items()
        )
        print(f"Wrote {summary}, plus zipped CSV equivalents; source-rich copies are in {args.debug_dir}.")
    else:
        try:
            save_parquets([], [], args.data_dir, debug_dir=args.debug_dir)
            print("No new workbooks; refreshed clean datasets from debug Parquets.")
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
