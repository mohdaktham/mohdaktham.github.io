# Retail Sales Analytics in SQL

**Tools:** SQL (SQLite — CTEs, window functions, NTILE, cohorts) · Python for ETL · **Data:** Superstore retail dataset (9,994 order lines, 2015–2018)

## Business question
A national retailer wants to know: where is profit actually made, which discounting behaviour destroys margin, and which customers are worth retention spend?

## What I did
- **Normalized a flat 21-column CSV into a 4-table relational schema** (`customers`, `products`, `orders`, `order_items`) with indexes — `build_db.py`
- Wrote **7 production-style analytical queries** (`analysis_queries.sql`) covering YoY growth, profitability ranking, discount-loss diagnosis, 12-month cohort retention, RFM customer segmentation, and shipping SLA monitoring
- `run_queries.py` executes the full suite and exports every result to `outputs/` as CSVs

## Key findings
- Revenue grew from **$484K (2015) to $733K (2018)**, +29.5% and +20.4% in the last two years; profit margin improved from 10.2% → 12.7%
- **Tables lose $17.7K despite heavy discounting (26% avg)** — Bookcases and Supplies also run negative. Recommendation: cap Table discounts at 15%
- **Copiers are the hidden star**: only 8th in revenue but #1 in profit ($55.6K at a 37% margin)
- RFM segmentation found **82 "At Risk" customers averaging $4,444 lifetime sales** who haven't ordered in ~200 days — the highest-ROI win-back target
- 12-month repeat-purchase rate for the 2015 cohort is **69%**, rising for later cohorts

## SQL techniques demonstrated
`JOIN` across a normalized schema · CTEs · `LAG`/`RANK`/`ROW_NUMBER`/`NTILE` window functions · conditional aggregation · `julianday` date math · `HAVING` filters

## Run it
```bash
pip install pandas
python build_db.py      # builds superstore.db from superstore.csv
python run_queries.py   # runs all 7 queries, exports to outputs/
```
