# Excel KPI Dashboard — Superstore Sales

**Tools:** Advanced Excel (live formulas, native charts, auto-filter) built programmatically with Python/openpyxl · **Data:** Superstore retail dataset (2015–2018)

## What it is
A three-sheet executive dashboard workbook (`Superstore_KPI_Dashboard.xlsx`):

- **Dashboard** — 6 KPI cards (Revenue, Profit, Margin, Orders, AOV, Best Month) plus 4 native Excel charts: monthly revenue trend, sales & profit by category, revenue by segment, sales by region
- **Data** — clean monthly/category/segment/region aggregates that feed every KPI
- **Top Products** — sortable, filterable sub-category table with live margin formulas

## Why it matters for a BA role
- **Every KPI is a live Excel formula** (`SUM`, ratio margins, `MAX`) referencing the Data sheet — change the data and the whole dashboard recalculates. No hardcoded numbers.
- Delivered with **zero formula errors** (validated via automated LibreOffice recalculation)
- Follows finance formatting conventions: `$#,##0` currency, one-decimal percentages, negatives in parentheses

## Headline numbers
Total revenue **$2.30M**, profit **$286K** (12.5% margin) across 5,009 orders; Technology is the top category; the West region leads sales.

## Files
`Superstore_KPI_Dashboard.xlsx` (deliverable) · `build_dashboard.py` (reproducible build script)
