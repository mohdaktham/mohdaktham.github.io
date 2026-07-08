# BC Housing Completions Forecast (Production Model + Power BI)

**Tools:** Python (pandas, scikit-learn Ridge), time-series feature engineering, Power BI · **Data:** 36+ years of CMHC housing data merged with economic indicators (mortgage rates, policy rate, building permits)

**Context:** Built as Analytics Student Consultant for **BC Housing** (Jan 2026–present) — a real production forecasting system used by government stakeholders.

## What it does
Forecasts monthly housing completions 36 months ahead for every BC regional district (Total / Multi-unit / Single-detached), with calibrated uncertainty bands and rate-scenario analysis, feeding an interactive Power BI dashboard.

## Technical highlights
- **Pooled Ridge regression (v13)** on level-scaled, leakage-free features: target lags, under-construction pipeline lags, seasonal encodings, and 12-month mortgage-rate changes with a 6-month lag
- Scaling uses only past data (shifted trailing means) so districts of very different sizes pool legitimately — no look-ahead leakage
- **Backtested on 12 unseen months: 11.1% WAPE vs 20.7% for the naive benchmark** on the BC total series; the model beats naive on the large majority of the 24 regional series
- Empirical prediction intervals (50/80/95%) — 83% of holdout actuals landed inside the 80% band
- Scenario engine: baseline vs ±100bp mortgage-rate paths; rate-sensitivity table quantifies % forecast change per +100bp
- Pipeline anchor: forecasts cross-checked against units physically under construction (18-month conversion ratios)

## Deliverables
| File | Purpose |
|---|---|
| `BC_Housing_Forecast_v13_production.py` | Self-contained production pipeline (509 lines) — writes 8 Power BI CSVs |
| `PBI_Unified_Dashboard.csv` + 7 companion CSVs | Forecasts, scenarios, backtests, diagnostics, rate sensitivity |
| `PowerBI_Upgrade_Guide_v13.md` | Stakeholder documentation for wiring the model into the .pbix |
| `BC_Housing_Model_Card_v13.docx` | Model card: method, assumptions, validation |

*Note: the source CMHC workbook is not included here for data-sharing reasons; the script and outputs demonstrate the full pipeline.*
