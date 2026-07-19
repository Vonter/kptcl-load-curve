# kptcl-load-curve

Archive and dataset of daily load-curve reports published by the [Karnataka Power Transmission Corporation Limited (KPTCL)](https://loadcurve.kptcl.net/LoadCurveUpload/lcdownloadview.asp). The source `.xls` workbooks are normalized into analysis-ready Parquet datasets, with zipped CSV equivalents for the five tabular datasets.

Explore the data [visualized as charts](https://kptcl-load-curve.pages.dev).

## Data

- Hourly grid load and frequency: [Parquet](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl.parquet) or [zipped CSV](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl.csv.zip)
- Daily generating-station capacity and generation: [Parquet](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl-stations.parquet) or [zipped CSV](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl-stations.csv.zip)
- Daily reservoir levels, storage, inflow, and discharge: [Parquet](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl-reservoirs.parquet) or [zipped CSV](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl-reservoirs.csv.zip)
- Generator and major-line outages: [Parquet](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl-outages.parquet) or [zipped CSV](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl-outages.csv.zip)
- Tidy metrics from the transposed auxiliary daily-summary sheets: [Parquet](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl-daily-summary.parquet) or [zipped CSV](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl-daily-summary.csv.zip)
- Report sections: [Parquet](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl-report-sections.parquet), typed, row-grouped snapshots of every populated workbook section, including dashboard content without a stable semantic schema.

All tables use `report_date` as their shared daily key. See [DATA.md](DATA.md) for coverage, schemas, units, and parsing notes.

## Scripts

- [fetch.py](fetch.py): Fetches raw KPTCL workbook Excel files.
- [parse.py](parse.py): Parses workbook Excel files and writes the Parquet and zipped CSV datasets.

## License

This kptcl-load-curve dataset is made available under the Open Database License: http://opendatacommons.org/licenses/odbl/1.0/. 
Some individual contents of the database are under copyright by KPTCL.

You are free:

* **To share**: To copy, distribute and use the database.
* **To create**: To produce works from the database.
* **To adapt**: To modify, transform and build upon the database.

As long as you:

* **Attribute**: You must attribute any public use of the database, or works produced from the database, in the manner specified in the ODbL. For any use or redistribution of the database, or works produced from it, you must make clear to others the license of the database and keep intact any notices on the original database.
* **Share-Alike**: If you publicly use any adapted version of this database, or works produced from an adapted database, you must also offer that adapted database under the ODbL.
* **Keep open**: If you redistribute the database, or an adapted version of it, then you may use technological measures that restrict the work (such as DRM) as long as you also redistribute a version without such measures.

## Generating

Python 3.11 or later is required. Install with uv or pip:

```sh
uv sync
# or: python3 -m pip install -r requirements.txt
```

The normal incremental update is:

```sh
python3 fetch.py
python3 parse.py
```

`fetch.py` downloads each date after the latest `report_date` in `data/kptcl.parquet`, through yesterday. `parse.py` then parses raw workbooks after that same date, appends their rows, and removes fully duplicate rows from the Parquet datasets. Both commands report a no-op when the archive is current.

## Credits

- [KPTCL Load Curve portal](https://loadcurve.kptcl.net/LoadCurveUpload/lcdownloadview.asp)

## AI Declaration

Components of this repository, including code and documentation, were written with assistance from AI tools.
