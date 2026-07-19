# kptcl-load-curve

The repository contains multiple Parquet and zipped CSV datasets parsed from [KPTCL's daily `.xls` load-curve reports](https://loadcurve.kptcl.net/LoadCurveUpload/lcdownloadview.asp).

`report_date` is the shared key for the datasets. Rows are sorted by `report_date` descending. Secondary identifiers such as `observed_at`, `station`, `reservoir`, `system`, and `asset` are ascending where applicable. Exact duplicate rows are removed.

## Load Curve

Available as [Parquet](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl.parquet) and [Zipped CSV](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl.csv.zip)

| # | Column | Type | Description |
|---|--------|------|-------|
| 1 | `report_date` | timestamp | Date of the daily KPTCL report. |
| 2 | `observed_at` | timestamp | Observation timestamp derived from `report_date` and `report_hour`. |
| 3 | `report_hour` | int64 | Hour label from the report, from 0 through 24. Hour 24 maps to midnight on the following day in `observed_at`. |
| 4 | `grid_load_mw` | double | Karnataka grid load in megawatts. |
| 5 | `frequency_hz` | double | Grid frequency in hertz. |

`D01JUL2013.xls` contains no hourly load section, so that date is represented in the other applicable datasets but has no invented load rows. `D31MAR2017.xls` contains source hours 1 through 24 but no hour 0, and `D15AUG2020.xls` contains load without frequency; those source omissions remain null or absent. When a workbook contains a duplicate experimental load sheet, the parser selects the most complete curve with plausible frequency values and writes only one row per source hour.

## Stations

Available as [Parquet](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl-stations.parquet) and [Zipped CSV](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl-stations.csv.zip)

| # | Column | Type | Description |
|---|--------|------|-------|
| 1 | `report_date` | timestamp | Date of the daily KPTCL report. |
| 2 | `category` | string | Nearest source section heading, such as a generation or exchange category. |
| 3 | `station` | string | Human-friendly normalized station, exchange, subtotal, or total label. |
| 4 | `installed_units` | double | Number of installed generating units. |
| 5 | `installed_capacity_mw` | double | Installed capacity in megawatts, including values carrying source footnote markers. |
| 6 | `units_generating` | double | Number of units generating on the report date. |
| 7 | `generation_at_state_max_mw` | double | Generation in megawatts at the state maximum-demand interval. |
| 8 | `generation_at_state_min_mw` | double | Generation in megawatts at the state minimum-demand interval. |
| 9 | `energy_generated_mu` | double | Energy generated or exchanged in million units. |
| 10 | `record_max_mw` | double | Maximum generation record in megawatts when reported. |

Rows include individual stations, exchanges, source categories, subtotals, and the grand total when they contain numeric generation data. `station` is a human-friendly normalized label.

## Reservoirs

Available as [Parquet](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl-reservoirs.parquet) and [Zipped CSV](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl-reservoirs.csv.zip)

| # | Column | Type | Description |
|---|--------|------|-------|
| 1 | `report_date` | timestamp | Date of the daily KPTCL report. |
| 2 | `observed_at` | timestamp | Reservoir observation time read from the report heading. Impossible month-end ordinals in two source headings use the following morning implied by the report sequence. |
| 3 | `reservoir` | string | Normalized reservoir name. |
| 4 | `energy_capacity_mu` | double | Reservoir energy capacity in million units. |
| 5 | `full_reservoir_level` | double | Full reservoir level. See the adjacent unit column. |
| 6 | `full_reservoir_level_unit` | string | Unit printed for full reservoir level, generally feet or metres. |
| 7 | `capacity_mcft` | double | Reservoir capacity in million cubic feet. |
| 8 | `previous_year_level` | double | Reservoir level for the comparison year. |
| 9 | `current_level` | double | Reservoir level for the current report year. |
| 10 | `previous_year_live_capacity_mcft` | double | Live capacity for the comparison year, in million cubic feet. |
| 11 | `current_live_capacity_mcft` | double | Current live capacity in million cubic feet. |
| 12 | `previous_year_equivalent_energy_mu` | double | Equivalent energy for the comparison year, in million units. |
| 13 | `current_equivalent_energy_mu` | double | Current equivalent energy in million units. |
| 14 | `previous_year_storage_percent` | double | Storage for the comparison year, as a percentage. |
| 15 | `current_storage_percent` | double | Current storage as a percentage. |
| 16 | `previous_year_inflow_cusecs` | double | Inflow for the comparison year, in cubic feet per second. |
| 17 | `current_inflow_cusecs` | double | Current inflow in cubic feet per second. |
| 18 | `previous_year_inflow_mu` | double | Inflow energy for the comparison year, in million units. |
| 19 | `current_inflow_mu` | double | Current inflow energy in million units. |
| 20 | `previous_year_discharge_cusecs` | double | Discharge for the comparison year, in cubic feet per second. |
| 21 | `current_discharge_cusecs` | double | Current discharge in cubic feet per second. |
| 22 | `previous_year_monthly_inflow_mcft` | double | Month-to-date inflow for the comparison year, in million cubic feet. |
| 23 | `current_monthly_inflow_mcft` | double | Current month-to-date inflow in million cubic feet. |
| 24 | `previous_year_monthly_inflow_mu` | double | Month-to-date inflow energy for the comparison year, in million units. |
| 25 | `current_monthly_inflow_mu` | double | Current month-to-date inflow energy in million units. |
| 26 | `previous_year_progressive_inflow_mcft` | double | Progressive inflow for the comparison year, in million cubic feet, when present. |
| 27 | `current_progressive_inflow_mcft` | double | Current progressive inflow in million cubic feet, when present. |

The source reports Linganamakki, Supa, and Mani. `previous_year_*` and `current_*` retain KPTCL's side-by-side comparison values rather than calculating year-over-year metrics.

## Outages

Available as [Parquet](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl-outages.parquet) and [Zipped CSV](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl-outages.csv.zip)

| # | Column | Type | Description |
|---|--------|------|-------|
| 1 | `report_date` | timestamp | Date of the daily KPTCL report. |
| 2 | `system` | string | Normalized system: `central_generator`, `state_generator`, or `major_line`. |
| 3 | `outage_type` | string | Normalized outage classification. |
| 4 | `asset` | string | Generator or transmission-line label. |
| 5 | `details` | string | Outage details as printed in the report. |
| 6 | `from_time` | string | Reported outage start value. |
| 7 | `to_time` | string | Reported outage end value. |
| 8 | `remarks` | string | Additional source remarks. |

Generator outages are separated into planned and forced events. Major-line entries retain line-clear, outage, over-voltage, and power-regulation classifications. Time fields remain strings because the source uses mixed formats, open-ended intervals, and free text.

## Daily Summary

Available as [Parquet](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl-daily-summary.parquet) and [Zipped CSV](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl-daily-summary.csv.zip)

| # | Column | Type | Description |
|---|--------|------|-------|
| 1 | `report_date` | timestamp | Date of the daily KPTCL report. |
| 2 | `category` | string | Normalized metric family: `generation`, `reservoir`, `exchange`, or `grid`. |
| 3 | `entity` | string | Human-readable station, reservoir, exchange, or grid entity. |
| 4 | `metric` | string | Normalized metric identifier. |
| 5 | `unit` | string | Printed or inferred unit: generally `MW`, `MU`, `Hz`, or `cusecs`. |
| 6 | `value` | double | Numeric source value. |

Some workbooks contain an auxiliary sheet with one wide row of daily values. This dataset pivots that sheet into tidy rows with normalized identities. It is present only where the source includes that auxiliary summary (workbooks prior to 2024-08-24) and its absence on other dates is not imputed.

## Report Sections

Available as [Parquet](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl-report-sections.parquet) and [Zipped CSV](https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data/kptcl-report-sections.csv.zip)

| # | Column | Type | Description |
|---|--------|------|-------|
| 1 | `report_date` | timestamp | Date of the daily KPTCL report. |
| 2 | `section_type` | string | Normalized logical section identifier. |
| 3 | `rows` | list of structs | Populated source rows in worksheet order, with typed `text`, `number`, `boolean`, and `datetime` cell lists. |

This table preserves all populated source cells, including headers and structure from sections that are too variable for a reliable fixed semantic schema. Recognized sections include reservoir and station source tables, hourly curves, daily summaries, minor-reservoir flows, reservoir availability, hydro generation, generation averages, progressive consumption, central schedules, generator and line outages, unscheduled curtailment, rainfall, projections and actuals, dam levels, energy exports and purchases, previous-year references, footnotes, historical IEX reference sheets, and embedded Form-D schedules. Any populated cell not claimed by a recognized layout is retained under `unclassified`.

The section table intentionally overlaps some information in the semantic datasets, while the other five files remain the preferred analysis tables. Each item in `rows` represents one populated worksheet row. Its four typed lists contain only `{column, value}` structs, so values stay directly queryable in Arrow-compatible tools without nullable `*_value` fields. Worksheet row numbers and blank row gaps are intentionally omitted; list order retains the source order.

Current `section_type` values are `annual_projection_and_actuals`, `central_generation_schedule`, `central_generator_outages`, `daily_summary`, `dam_levels`, `embedded_form_d_schedule`, `energy_exports`, `energy_purchases`, `footnotes_and_signoff`, `generation_averages`, `historical_energy_import_reference`, `hourly_load_curve`, `hydro_generation`, `major_line_clears_and_outages`, `major_line_voltage_regulation`, `major_reservoir_availability`, `minor_reservoir_flows`, `monthly_projection_and_actuals`, `previous_year_reference`, `progressive_state_consumption`, `rainfall`, `reservoir_details`, `state_generator_outages`, `stations`, `unclassified`, and `unscheduled_load_curtailment`.

`rows` contains the cached values exposed by the XLS file. Formula expressions, formatting, and merged-cell definitions are not reproduced.

## Caveats

- Daily publication is not guaranteed, and some dates are absent from the source archive.
- KPTCL workbook layouts and labels vary over time. A field may be null when a report omits it or formats it differently.
