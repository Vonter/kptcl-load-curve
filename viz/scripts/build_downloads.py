"""Build the download catalog and bounded dataset previews for the dashboard."""

from __future__ import annotations

import json
import math
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
OUTPUT = ROOT / "viz" / "static" / "data" / "downloads.json"

# Enough rows for a useful, scrollable preview without sending entire datasets
# (some contain more than 100,000 records) to every visitor.
PREVIEW_ROWS = 1_000
PREVIEW_LENGTH = 180

DATASETS = (
	(
		"load-curve",
		"System load",
		"Hourly Karnataka grid load and frequency readings.",
		"kptcl.parquet",
	),
	(
		"stations",
		"Generation stations",
		"Daily capacity, generation and energy by station.",
		"kptcl-stations.parquet",
	),
	(
		"reservoirs",
		"Reservoirs",
		"Daily levels, storage, inflow and discharge by reservoir.",
		"kptcl-reservoirs.parquet",
	),
	(
		"outages",
		"Outages",
		"Generator and major-line outage records.",
		"kptcl-outages.parquet",
	),
	(
		"daily-summary",
		"Daily summary",
		"Tidy metrics extracted from auxiliary summary sheets.",
		"kptcl-daily-summary.parquet",
	),
	(
		"report-sections",
		"Report sections",
		"Typed snapshots of every populated workbook section.",
		"kptcl-report-sections.parquet",
	),
)


def json_value(value: Any) -> Any:
	if value is None:
		return None
	if isinstance(value, float) and not math.isfinite(value):
		return None
	if isinstance(value, (date, datetime, time)):
		return value.isoformat()
	if isinstance(value, bytes):
		return value.hex()
	if isinstance(value, dict):
		return {str(key): json_value(item) for key, item in value.items()}
	if isinstance(value, (list, tuple)):
		return [json_value(item) for item in value]
	if hasattr(value, "item"):
		return json_value(value.item())
	return value


def preview_value(value: Any) -> str | int | float | bool | None:
	value = json_value(value)
	if isinstance(value, float):
		return float(f"{value:.12g}")
	if value is None or isinstance(value, (int, float, bool)):
		return value
	text = value if isinstance(value, str) else json.dumps(value, separators=(",", ":"))
	return text if len(text) <= PREVIEW_LENGTH else f"{text[: PREVIEW_LENGTH - 1]}…"


def file_info(path: Path) -> dict[str, Any] | None:
	return {"file": path.name, "bytes": path.stat().st_size} if path.is_file() else None


def dataset_entry(
	dataset_id: str, label: str, description: str, filename: str
) -> dict[str, Any]:
	path = DATA_DIR / filename
	parquet = pq.ParquetFile(path)
	batch = next(parquet.iter_batches(batch_size=PREVIEW_ROWS), None)
	sample = batch.to_pylist() if batch is not None else []
	csv_path = path.with_suffix(".csv.zip")
	return {
		"id": dataset_id,
		"label": label,
		"description": description,
		"rows": parquet.metadata.num_rows,
		"columns": [
			{"name": field.name, "type": str(field.type)} for field in parquet.schema_arrow
		],
		"parquet": file_info(path),
		"csv": file_info(csv_path),
		"preview": [
			{name: preview_value(value) for name, value in row.items()} for row in sample
		],
	}


def main() -> None:
	payload = {"datasets": [dataset_entry(*dataset) for dataset in DATASETS]}
	OUTPUT.parent.mkdir(parents=True, exist_ok=True)
	OUTPUT.write_text(
		json.dumps(payload, separators=(",", ":"), ensure_ascii=False), encoding="utf-8"
	)
	print(f"Wrote {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size / 1024:.1f} KiB)")


if __name__ == "__main__":
	main()
