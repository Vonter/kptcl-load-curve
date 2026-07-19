#!/usr/bin/env python3
"""Download KPTCL daily load-curve workbooks."""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
DOWNLOAD_URL = "https://loadcurve.kptcl.net/LoadCurveUpload/lcdownloadFl.asp"
MONTHS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
TIMEOUT = 90
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"


class DownloadError(RuntimeError):
    pass


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("dates must use YYYY-MM-DD") from exc


def workbook_name(day: date) -> str:
    return f"D{day:%d}{MONTHS[day.month - 1]}{day:%Y}.xls"


def date_range(start: date, end: date) -> list[date]:
    if end < start:
        raise ValueError("--end must not be earlier than --start")
    return [start + timedelta(days=offset) for offset in range((end - start).days + 1)]


def latest_report_date(path: Path) -> date | None:
    if not path.exists():
        return None
    values = pd.read_parquet(path, columns=["report_date"])["report_date"]
    return None if values.empty else pd.to_datetime(values).max().date()


def requested_dates(args: argparse.Namespace) -> list[date]:
    if args.dates and (args.start or args.end):
        raise ValueError("dates cannot be combined with --start or --end")
    if args.dates:
        return sorted(set(args.dates))
    if args.start or args.end:
        start, end = args.start or args.end, args.end or args.start
        return date_range(start, end)
    end = datetime.now().astimezone().date() - timedelta(days=1)
    latest = latest_report_date(args.parquet)
    if latest and latest >= end:
        return []
    return date_range(latest + timedelta(days=1) if latest else end, end)


def fetch_workbook(day: date, session: requests.Session) -> bytes:
    payload = {"Lstday": f"{day:%d}", "Lstmth": MONTHS[day.month - 1], "Lstyr": f"{day:%Y}"}
    response = session.post(DOWNLOAD_URL, data=payload, timeout=TIMEOUT)
    response.raise_for_status()
    expected = workbook_name(day).lower()
    soup = BeautifulSoup(response.text, "html.parser")
    href = next((a["href"] for a in soup.find_all("a", href=True) if a["href"].lower().endswith(expected)), None)
    if not href:
        raise DownloadError(f"KPTCL has no workbook link for {day.isoformat()}")
    response = session.get(urljoin(DOWNLOAD_URL, href), timeout=TIMEOUT)
    response.raise_for_status()
    if not response.content.startswith(b"\xd0\xcf\x11\xe0"):
        raise DownloadError(f"KPTCL returned a non-XLS response for {day.isoformat()}")
    return response.content


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dates", nargs="*", type=parse_date, metavar="YYYY-MM-DD")
    parser.add_argument("--start", type=parse_date, help="first date in an inclusive range")
    parser.add_argument("--end", type=parse_date, help="last date in an inclusive range")
    parser.add_argument("--force", action="store_true", help="replace workbooks already in the raw directory")
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "raw", help="workbook directory (default: raw)")
    parser.add_argument("--parquet", type=Path, default=ROOT / "data/kptcl.parquet", help="freshness reference (default: data/kptcl.parquet)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        days = requested_dates(args)
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if not days:
        print("No new dates to fetch.")
        return 0
    args.raw_dir.mkdir(parents=True, exist_ok=True)
    failures = 0
    with requests.Session() as session:
        session.headers.update({"User-Agent": USER_AGENT})
        for day in days:
            path = args.raw_dir / workbook_name(day)
            if path.exists() and not args.force:
                print(f"{day}: cached {path.name}")
                continue
            try:
                path.write_bytes(fetch_workbook(day, session))
                print(f"{day}: downloaded {path.name}")
            except (requests.RequestException, DownloadError, OSError) as exc:
                failures += 1
                print(f"ERROR {day}: {exc}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
