"""Build the compact browser dataset used by the static dashboard.

The Parquets remain the source of truth. This script keeps the frontend payload
small by retaining full daily history, recent hourly detail, and current report
snapshots instead of shipping six analytical Parquets to every browser.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
OUTPUT = ROOT / "viz" / "static" / "data" / "dashboard.json"
REPORTS_DIR = OUTPUT.parent / "reports"
HISTORICAL_OUTPUT = OUTPUT.parent / "historical.json"


def iso(value: Any) -> str:
	return pd.Timestamp(value).strftime("%Y-%m-%d")


def number(value: Any, digits: int = 3) -> float | None:
	if value is None or pd.isna(value):
		return None
	value = float(value)
	if not math.isfinite(value):
		return None
	return round(value, digits)


def string(value: Any) -> str | None:
	if value is None or pd.isna(value):
		return None
	value = str(value).strip()
	return value or None


def unique_by_date(frame: pd.DataFrame) -> pd.DataFrame:
	return frame.sort_values("report_date").drop_duplicates("report_date", keep="last")


def load_curve(frame: pd.DataFrame) -> list[dict[str, Any]]:
	return [
		{
			"hour": int(row.report_hour),
			"load": number(row.grid_load_mw),
			"frequency": number(row.frequency_hz),
		}
		for row in frame.itertuples()
	]


def outage_events(frame: pd.DataFrame) -> list[dict[str, Any]]:
	return [
		{
			"system": row.system,
			"type": row.outage_type,
			"asset": row.asset,
			"details": string(row.details),
			"from": string(row.from_time),
			"to": string(row.to_time),
			"remarks": string(row.remarks),
		}
		for row in frame.itertuples()
	]


def summary_metrics(frame: pd.DataFrame, include_metric: bool = False) -> list[dict[str, Any]]:
	return [
		{
			"entity": row.entity,
			**({"metric": row.metric} if include_metric else {}),
			"value": number(row.value),
			"unit": string(row.unit),
		}
		for row in frame.itertuples()
	]


def write_json(path: Path, payload: Any) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(
		json.dumps(payload, separators=(",", ":"), ensure_ascii=False), encoding="utf-8"
	)
	print(f"Wrote {path.relative_to(ROOT)} ({path.stat().st_size / 1024 / 1024:.2f} MiB)")


def load_report() -> dict[str, Any]:
	frame = pd.read_parquet(DATA_DIR / "kptcl.parquet")
	daily = (
		frame.groupby("report_date", as_index=False)
		.agg(
			peak_mw=("grid_load_mw", "max"),
			minimum_mw=("grid_load_mw", "min"),
			average_mw=("grid_load_mw", "mean"),
			min_hz=("frequency_hz", "min"),
			max_hz=("frequency_hz", "max"),
			average_hz=("frequency_hz", "mean"),
		)
		.sort_values("report_date")
	)
	peak_hours = frame.loc[
		frame.groupby("report_date")["grid_load_mw"].idxmax(), ["report_date", "report_hour"]
	].rename(columns={"report_hour": "peak_hour"})
	minimum_hours = frame.loc[
		frame.groupby("report_date")["grid_load_mw"].idxmin(), ["report_date", "report_hour"]
	].rename(columns={"report_hour": "minimum_hour"})
	daily = daily.merge(peak_hours, on="report_date", how="left").merge(
		minimum_hours, on="report_date", how="left"
	)
	latest_date = frame.report_date.max()
	recent = frame[frame.report_date >= latest_date - pd.Timedelta(days=45)].sort_values(
		["report_date", "report_hour"]
	)
	curve: dict[str, list[dict[str, Any]]] = {}
	for report_date, group in recent.groupby("report_date", sort=True):
		curve[iso(report_date)] = load_curve(group)
	return {
		"coverage": [iso(frame.report_date.min()), iso(latest_date)],
		"observations": int(len(frame)),
		"daily": [
			{
				"date": iso(row.report_date),
				"peak": number(row.peak_mw),
				"minimum": number(row.minimum_mw),
				"average": number(row.average_mw),
				"peakHour": int(row.peak_hour),
				"minimumHour": int(row.minimum_hour),
				"minHz": number(row.min_hz),
				"maxHz": number(row.max_hz),
				"averageHz": number(row.average_hz),
			}
			for row in daily.itertuples()
		],
		"curve": curve,
	}


def station_report() -> dict[str, Any]:
	frame = pd.read_parquet(DATA_DIR / "kptcl-stations.parquet")
	grand = unique_by_date(frame[frame.station == "Grand Total"])
	latest_date = frame.report_date.max()
	latest = frame[frame.report_date == latest_date].drop_duplicates(
		["station", "category"], keep="last"
	)
	previous_date = frame.loc[frame.report_date < latest_date, "report_date"].max()
	previous = (
		frame[frame.report_date == previous_date]
		.drop_duplicates("station", keep="last")
		.set_index("station")
	)
	aggregates = {
		"Grand Total",
		"Total",
		"Total Energy from IPPs",
		"Total NCE",
		"Total NCE (Provisional)",
	}
	assets: list[dict[str, Any]] = []
	for row in latest.itertuples():
		if row.station in aggregates:
			continue
		previous_energy = (
			previous.loc[row.station, "energy_generated_mu"]
			if row.station in previous.index
			else None
		)
		assets.append(
			{
				"station": row.station,
				"category": row.category,
				"capacity": number(row.installed_capacity_mw),
				"units": number(row.units_generating),
				"generation": number(row.generation_at_state_max_mw),
				"energy": number(row.energy_generated_mu),
				"previousEnergy": number(previous_energy),
			}
		)
	assets.sort(key=lambda item: item["energy"] if item["energy"] is not None else -math.inf, reverse=True)
	nce_names = sorted(item["station"] for item in assets if item["station"].startswith("NCE -"))
	other_names = [
		item["station"]
		for item in assets
		if not item["station"].startswith("NCE -") and (item["energy"] or 0) > 0
	][:8]
	contributor_names = other_names + nce_names
	contributor_frame = frame[
		(frame.report_date >= latest_date - pd.Timedelta(days=365))
		& frame.station.isin(contributor_names)
	].drop_duplicates(["report_date", "station"], keep="last")
	contributor_history = contributor_frame.pivot_table(
		index="report_date", columns="station", values="energy_generated_mu", aggfunc="last"
	).reset_index().sort_values("report_date")
	grand_latest = grand.iloc[-1]
	return {
		"coverage": [iso(frame.report_date.min()), iso(latest_date)],
		"reportDate": iso(latest_date),
		"previousDate": iso(previous_date),
		"history": [
			{
				"date": iso(row.report_date),
				"capacity": number(row.installed_capacity_mw),
				"energy": number(row.energy_generated_mu),
				"maximum": number(row.generation_at_state_max_mw),
				"minimum": number(row.generation_at_state_min_mw),
			}
			for row in grand.itertuples()
		],
		"totals": {
			"capacity": number(grand_latest.installed_capacity_mw),
			"energy": number(grand_latest.energy_generated_mu),
			"maximum": number(grand_latest.generation_at_state_max_mw),
		},
		"assets": assets,
		"contributors": {
			"nce": nce_names,
			"other": other_names,
			"history": [
				{
					"date": iso(row["report_date"]),
					**{
						name: number(row.get(name))
						for name in contributor_names
					},
				}
				for row in contributor_history.to_dict(orient="records")
			],
		},
	}


def station_snapshot(
	current: pd.DataFrame, previous: pd.DataFrame, year_ago: pd.DataFrame
) -> dict[str, Any]:
	current = current.drop_duplicates(["station", "category"], keep="last")
	previous_by_station = previous.drop_duplicates("station", keep="last").set_index("station")
	year_ago_by_station = year_ago.drop_duplicates("station", keep="last").set_index("station")
	aggregates = {
		"Grand Total",
		"Total",
		"Total Energy from IPPs",
		"Total NCE",
		"Total NCE (Provisional)",
	}
	assets: list[dict[str, Any]] = []
	for row in current.itertuples():
		if row.station in aggregates:
			continue
		previous_energy = (
			previous_by_station.loc[row.station, "energy_generated_mu"]
			if row.station in previous_by_station.index
			else None
		)
		year_ago_energy = (
			year_ago_by_station.loc[row.station, "energy_generated_mu"]
			if row.station in year_ago_by_station.index
			else None
		)
		assets.append(
			{
				"station": row.station,
				"category": row.category,
				"capacity": number(row.installed_capacity_mw),
				"units": number(row.units_generating),
				"generation": number(row.generation_at_state_max_mw),
				"energy": number(row.energy_generated_mu),
				"previousEnergy": number(previous_energy),
				"yearAgoEnergy": number(year_ago_energy),
			}
		)
	assets.sort(
		key=lambda item: item["energy"] if item["energy"] is not None else -math.inf,
		reverse=True,
	)
	nce_names = sorted(item["station"] for item in assets if item["station"].startswith("NCE -"))
	other_names = [
		item["station"]
		for item in assets
		if not item["station"].startswith("NCE -") and (item["energy"] or 0) > 0
	][:8]
	grand = current[current.station == "Grand Total"]
	grand_row = grand.iloc[-1] if not grand.empty else None
	return {
		"totals": {
			"capacity": number(grand_row.installed_capacity_mw) if grand_row is not None else None,
			"energy": number(grand_row.energy_generated_mu) if grand_row is not None else None,
			"maximum": number(grand_row.generation_at_state_max_mw) if grand_row is not None else None,
		},
		"assets": assets,
		"contributors": {"nce": nce_names, "other": other_names},
	}


def reservoir_report() -> dict[str, Any]:
	frame = pd.read_parquet(DATA_DIR / "kptcl-reservoirs.parquet").sort_values(
		["report_date", "reservoir"]
	)
	frame = frame.drop_duplicates(["report_date", "reservoir"], keep="last")
	latest_date = frame.report_date.max()
	return {
		"coverage": [iso(frame.report_date.min()), iso(latest_date)],
		"reportDate": iso(latest_date),
		"reservoirs": sorted(frame.reservoir.unique().tolist()),
		"history": [
			{
				"date": iso(row.report_date),
				"reservoir": row.reservoir,
				"storage": number(row.current_storage_percent),
				"previousStorage": number(row.previous_year_storage_percent),
				"inflow": number(row.current_inflow_cusecs),
				"discharge": number(row.current_discharge_cusecs),
				"energy": number(row.current_equivalent_energy_mu),
				"level": number(row.current_level),
				"fullLevel": number(row.full_reservoir_level),
				"levelUnit": string(row.full_reservoir_level_unit),
			}
			for row in frame.itertuples()
		],
	}


def outage_report() -> dict[str, Any]:
	frame = pd.read_parquet(DATA_DIR / "kptcl-outages.parquet")
	latest_date = frame.report_date.max()
	daily = frame.groupby("report_date").size().rename("total").to_frame()
	for label, mask in {
		"planned": frame.outage_type == "planned",
		"forced": frame.outage_type == "forced",
		"lines": frame.system == "major_line",
		"regulation": frame.outage_type == "over_voltage_or_power_regulation",
	}.items():
		daily[label] = frame[mask].groupby("report_date").size()
	daily = daily.fillna(0).astype(int).reset_index().sort_values("report_date")
	events = frame[frame.report_date == latest_date].copy()
	return {
		"coverage": [iso(frame.report_date.min()), iso(latest_date)],
		"reportDate": iso(latest_date),
		"history": [
			{
				"date": iso(row.report_date),
				"total": int(row.total),
				"planned": int(row.planned),
				"forced": int(row.forced),
				"lines": int(row.lines),
				"regulation": int(row.regulation),
			}
			for row in daily.itertuples()
		],
		"events": outage_events(events),
	}


def summary_report() -> dict[str, Any]:
	frame = pd.read_parquet(DATA_DIR / "kptcl-daily-summary.parquet")
	latest_date = frame.report_date.max()
	load = pd.read_parquet(DATA_DIR / "kptcl.parquet")
	curve = load[load.report_date == latest_date].sort_values("report_hour")
	grid = frame[frame.category == "grid"].pivot_table(
		index="report_date", columns="metric", values="value", aggfunc="last"
	)
	grid = grid.reset_index().sort_values("report_date")
	generation = frame[
		(frame.report_date == latest_date)
		& (frame.category == "generation")
		& (frame.metric == "energy_generated")
	].sort_values("value", ascending=False)
	exchange = frame[(frame.report_date == latest_date) & (frame.category == "exchange")].sort_values(
		"value", ascending=False
	)
	return {
		"coverage": [iso(frame.report_date.min()), iso(latest_date)],
		"reportDate": iso(latest_date),
		"reportDates": int(frame.report_date.nunique()),
		"curve": load_curve(curve),
		"grid": [
			{
				"date": iso(row.report_date),
				"energy": number(getattr(row, "energy_consumed", None)),
				"maximumDemand": number(getattr(row, "maximum_demand", None)),
				"minimumDemand": number(getattr(row, "minimum_demand", None)),
				"maximumFrequency": number(getattr(row, "maximum_frequency", None)),
				"minimumFrequency": number(getattr(row, "minimum_frequency", None)),
			}
			for row in grid.itertuples()
		],
		"generation": summary_metrics(generation),
		"exchange": summary_metrics(exchange, include_metric=True),
	}


def cell_count(rows: Any) -> int:
	if rows is None or not isinstance(rows, (list, tuple)):
		return 0
	total = 0
	for row in rows:
		if not isinstance(row, dict):
			continue
		for cell_type in ("text", "number", "boolean", "datetime"):
			cells = row.get(cell_type)
			if cells is not None:
				total += len(cells)
	return total


def section_report() -> dict[str, Any]:
	frame = pd.read_parquet(DATA_DIR / "kptcl-report-sections.parquet")
	frame["row_count"] = frame.rows.map(lambda rows: len(rows) if isinstance(rows, (list, tuple)) else 0)
	frame["cell_count"] = frame.rows.map(cell_count)
	latest_date = frame.report_date.max()
	daily = (
		frame.groupby("report_date", as_index=False)
		.agg(sections=("section_type", "nunique"), cells=("cell_count", "sum"))
		.sort_values("report_date")
	)
	totals = (
		frame.groupby("section_type", as_index=False)
		.agg(
			reports=("report_date", "nunique"),
			first=("report_date", "min"),
			last=("report_date", "max"),
			cells=("cell_count", "sum"),
		)
		.sort_values("reports", ascending=False)
	)
	coverage = frame.assign(year=frame.report_date.dt.year).groupby(["section_type", "year"])[
		"report_date"
	].nunique()
	years = list(range(int(frame.report_date.dt.year.min()), int(frame.report_date.dt.year.max()) + 1))
	latest = frame[frame.report_date == latest_date].sort_values("section_type")
	return {
		"coverage": [iso(frame.report_date.min()), iso(latest_date)],
		"reportDate": iso(latest_date),
		"years": years,
		"history": [
			{"date": iso(row.report_date), "sections": int(row.sections), "cells": int(row.cells)}
			for row in daily.itertuples()
		],
		"sections": [
			{
				"section": row.section_type,
				"reports": int(row.reports),
				"first": iso(row.first),
				"last": iso(row.last),
				"cells": int(row.cells),
				"byYear": [int(coverage.get((row.section_type, year), 0)) for year in years],
			}
			for row in totals.itertuples()
		],
		"latest": [
			{
				"section": row.section_type,
				"rows": int(row.row_count),
				"cells": int(row.cell_count),
			}
			for row in latest.itertuples()
		],
	}


def historical_report() -> dict[str, Any]:
	load = pd.read_parquet(DATA_DIR / "kptcl.parquet").sort_values("report_date")
	load["month"] = load.report_date.dt.to_period("M")
	monthly_load = (
		load.groupby("month", as_index=False)
		.agg(
			date=("report_date", "max"),
			peak=("grid_load_mw", "max"),
			minimum=("grid_load_mw", "min"),
			average=("grid_load_mw", "mean"),
			min_hz=("frequency_hz", "min"),
			max_hz=("frequency_hz", "max"),
			average_hz=("frequency_hz", "mean"),
		)
		.sort_values("date")
	)

	stations = pd.read_parquet(DATA_DIR / "kptcl-stations.parquet")
	grand = unique_by_date(stations[stations.station == "Grand Total"]).sort_values("report_date")
	grand["month"] = grand.report_date.dt.to_period("M")
	monthly_generation = (
		grand.groupby("month", as_index=False)
		.agg(
			date=("report_date", "max"),
			energy=("energy_generated_mu", "mean"),
			capacity=("installed_capacity_mw", "last"),
		)
		.sort_values("date")
	)

	station_assets = stations.drop_duplicates(["report_date", "station"], keep="last")
	generation_source_names = [
		"Grid imports",
		"RTPS",
		"Solar",
		"Wind",
		"BTPS",
		"UPCL",
		"Sharavathi",
		"Jindal",
	]
	generation_source_masks = [
		station_assets.station.str.startswith("Net CGS Import"),
		station_assets.station == "RTPS",
		station_assets.station.isin(["NCE - Solar", "NCE - Solar (10 MW)", "Solar (KPCL)"]),
		station_assets.station == "NCE - Wind",
		station_assets.station == "BTPS",
		station_assets.station == "UPCL",
		station_assets.station == "Sharavathi",
		station_assets.station == "Jindal",
	]
	daily_generation_sources: list[pd.DataFrame] = []
	for source, mask in zip(generation_source_names, generation_source_masks, strict=True):
		source_rows = (
			station_assets.loc[mask]
			.groupby("report_date")["energy_generated_mu"]
			.sum(min_count=1)
			.rename("energy")
			.reset_index()
		)
		source_rows["source"] = source
		daily_generation_sources.append(source_rows)
	generation_sources = pd.concat(daily_generation_sources, ignore_index=True)
	generation_sources["month"] = generation_sources.report_date.dt.to_period("M")
	monthly_generation_sources = (
		generation_sources.groupby(["month", "source"], as_index=False)
		.agg(energy=("energy", "mean"))
		.pivot_table(index="month", columns="source", values="energy", aggfunc="last")
		.reindex(columns=generation_source_names)
		.reset_index()
	)
	month_dates = (
		station_assets.assign(month=station_assets.report_date.dt.to_period("M"))
		.groupby("month", as_index=False)
		.agg(date=("report_date", "max"))
	)
	monthly_generation_sources = month_dates.merge(
		monthly_generation_sources, on="month", how="left"
	).sort_values("date")

	reservoirs = pd.read_parquet(DATA_DIR / "kptcl-reservoirs.parquet").drop_duplicates(
		["report_date", "reservoir"], keep="last"
	)
	reservoirs["month"] = reservoirs.report_date.dt.to_period("M")
	monthly_reservoirs = (
		reservoirs.groupby(["month", "reservoir"], as_index=False)
		.agg(date=("report_date", "max"), storage=("current_storage_percent", "mean"))
		.sort_values(["date", "reservoir"])
	)
	reservoir_history = (
		monthly_reservoirs.pivot_table(
			index="date", columns="reservoir", values="storage", aggfunc="last"
		)
		.reset_index()
		.sort_values("date")
	)
	reservoir_names = sorted(reservoirs.reservoir.unique().tolist())

	outages = pd.read_parquet(DATA_DIR / "kptcl-outages.parquet")
	daily_outages = outages.groupby("report_date").size().rename("total").to_frame()
	for label, mask in {
		"planned": outages.outage_type == "planned",
		"forced": outages.outage_type == "forced",
		"lines": outages.system == "major_line",
	}.items():
		daily_outages[label] = outages[mask].groupby("report_date").size()
	daily_outages = daily_outages.fillna(0).reset_index()
	daily_outages["month"] = daily_outages.report_date.dt.to_period("M")
	monthly_outages = (
		daily_outages.groupby("month", as_index=False)
		.agg(
			date=("report_date", "max"),
			total=("total", "sum"),
			planned=("planned", "sum"),
			forced=("forced", "sum"),
			lines=("lines", "sum"),
		)
		.sort_values("date")
	)

	return {
		"coverage": [iso(load.report_date.min()), iso(load.report_date.max())],
		"load": [
			{
				"date": iso(row.date),
				"peak": number(row.peak),
				"minimum": number(row.minimum),
				"average": number(row.average),
				"minHz": number(row.min_hz),
				"maxHz": number(row.max_hz),
				"averageHz": number(row.average_hz),
			}
			for row in monthly_load.itertuples()
		],
		"generation": [
			{
				"date": iso(row.date),
				"energy": number(row.energy),
				"capacity": number(row.capacity),
			}
			for row in monthly_generation.itertuples()
		],
		"generationSources": {
			"names": generation_source_names,
			"history": [
				{
					"date": iso(row["date"]),
					**{name: number(row.get(name)) for name in generation_source_names},
				}
				for row in monthly_generation_sources.to_dict(orient="records")
			],
		},
		"reservoirs": {
			"names": reservoir_names,
			"history": [
				{
					"date": iso(row["date"]),
					**{name: number(row.get(name)) for name in reservoir_names},
				}
				for row in reservoir_history.to_dict(orient="records")
			],
		},
		"outages": [
			{
				"date": iso(row.date),
				"total": int(row.total),
				"planned": int(row.planned),
				"forced": int(row.forced),
				"lines": int(row.lines),
			}
			for row in monthly_outages.itertuples()
		],
	}


def build_report_archives() -> list[str]:
	load = pd.read_parquet(DATA_DIR / "kptcl.parquet").sort_values(
		["report_date", "report_hour"]
	)
	stations = pd.read_parquet(DATA_DIR / "kptcl-stations.parquet").sort_values(
		["report_date", "station"]
	)
	outages = pd.read_parquet(DATA_DIR / "kptcl-outages.parquet").sort_values("report_date")
	summary = pd.read_parquet(DATA_DIR / "kptcl-daily-summary.parquet").sort_values("report_date")
	sections = pd.read_parquet(DATA_DIR / "kptcl-report-sections.parquet").sort_values(
		["report_date", "section_type"]
	)
	sections["row_count"] = sections.rows.map(
		lambda rows: len(rows) if isinstance(rows, (list, tuple)) else 0
	)
	sections["cell_count"] = sections.rows.map(cell_count)

	load_groups = {date: group for date, group in load.groupby("report_date", sort=True)}
	station_groups = {date: group for date, group in stations.groupby("report_date", sort=True)}
	station_dates = pd.DatetimeIndex(sorted(station_groups))
	outage_groups = {date: group for date, group in outages.groupby("report_date", sort=True)}
	summary_groups = {date: group for date, group in summary.groupby("report_date", sort=True)}
	section_groups = {date: group for date, group in sections.groupby("report_date", sort=True)}
	report_dates = sorted(
		set(load_groups)
		| set(station_groups)
		| set(outage_groups)
		| set(summary_groups)
		| set(section_groups)
	)

	REPORTS_DIR.mkdir(parents=True, exist_ok=True)
	previous_station = pd.DataFrame(columns=stations.columns)
	year_payload: dict[str, dict[str, Any]] = {}
	active_year: int | None = None

	def write_year(year: int, payload: dict[str, dict[str, Any]]) -> None:
		write_json(REPORTS_DIR / f"{year}.json", {"dates": payload})

	for report_date in report_dates:
		year = int(report_date.year)
		if active_year is None:
			active_year = year
		elif year != active_year:
			write_year(active_year, year_payload)
			year_payload = {}
			active_year = year
		date = iso(report_date)

		load_rows = load_groups.get(report_date)
		station_rows = station_groups.get(report_date)
		outage_rows = outage_groups.get(report_date)
		summary_rows = summary_groups.get(report_date)
		section_rows = section_groups.get(report_date)

		station_data = (
			station_snapshot(
				station_rows,
				previous_station,
				station_groups[station_dates[year_ago_position]]
				if (year_ago_position := station_dates.searchsorted(
					report_date - pd.DateOffset(years=1), side="right"
				) - 1) >= 0
				else pd.DataFrame(columns=stations.columns),
			)
			if station_rows is not None
			else {"totals": {}, "assets": [], "contributors": {"nce": [], "other": []}}
		)
		if station_rows is not None:
			previous_station = station_rows

		generation = (
			summary_rows[
				(summary_rows.category == "generation")
				& (summary_rows.metric == "energy_generated")
			].sort_values("value", ascending=False)
			if summary_rows is not None
			else pd.DataFrame()
		)
		exchange = (
			summary_rows[summary_rows.category == "exchange"].sort_values("value", ascending=False)
			if summary_rows is not None
			else pd.DataFrame()
		)

		year_payload[date] = {
			"load": {"curve": load_curve(load_rows) if load_rows is not None else []},
			"stations": station_data,
			"outages": {
				"events": outage_events(outage_rows) if outage_rows is not None else []
			},
			"summary": {
				"available": summary_rows is not None,
				"generation": summary_metrics(generation),
				"exchange": summary_metrics(exchange, include_metric=True),
			},
			"sections": {
				"latest": [
					{
						"section": row.section_type,
						"rows": int(row.row_count),
						"cells": int(row.cell_count),
					}
					for row in section_rows.itertuples()
				]
				if section_rows is not None
				else []
			},
		}

	if active_year is not None:
		write_year(active_year, year_payload)
	return [iso(date) for date in report_dates]


def main() -> None:
	report_dates = build_report_archives()
	historical = historical_report()
	payload = {
		"generatedFrom": "KPTCL daily load-curve Parquets",
		"reportDates": report_dates,
		"load": load_report(),
		"stations": station_report(),
		"reservoirs": reservoir_report(),
		"outages": outage_report(),
		"summary": summary_report(),
		"sections": section_report(),
	}
	write_json(OUTPUT, payload)
	write_json(HISTORICAL_OUTPUT, historical)


if __name__ == "__main__":
	main()
