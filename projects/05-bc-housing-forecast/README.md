# BC Housing Completions Forecast (Forecast Model + Power BI)

**Tools:** Python (pandas, scikit-learn Ridge), time-series feature engineering, Power BI · **Data:** 36+ years of CMHC housing data merged with economic indicators (mortgage rates, policy rate, building permits)

**Context:** Consulting engagement with **BC Housing** through Wilfrid Laurier University, January to August 2026, where I was a Data Analyst Consultant (part-time contract) on the project team. My part was the data preparation, the forecasting models and the Power BI build. The results and the dashboard were presented to agency staff and programme leads.

## What it does
Forecasts monthly housing completions 36 months ahead for every BC regional district (Total / Multi-unit / Single-detached), with calibrated uncertainty bands and rate-scenario analysis, feeding an interactive Power BI dashboard.

## Technical highlights
- **Pooled Ridge regression (v13)** on level-scaled, leakage-free features: target lags, under-construction pipeline lags, seasonal encodings, and 12-month mortgage-rate changes with a 6-month lag
- Scaling uses only past data (shifted trailing means), so districts of very different sizes pool legitimately with no look-ahead leakage
- **Backtested on 12 unseen months: 11.1% WAPE vs 20.7% for the naive benchmark** on the BC total series; the model beats naive on the large majority of the 24 regional series
- Empirical prediction intervals (50/80/95%): 83% of holdout actuals landed inside the 80% band
- Scenario engine: baseline vs ±100bp mortgage-rate paths; rate-sensitivity table quantifies % forecast change per +100bp
- Pipeline anchor: forecasts cross-checked against units physically under construction (18-month conversion ratios)

## What was delivered
- A self-contained forecasting pipeline that writes eight data feeds for Power BI: forecasts, scenarios, backtests, diagnostics and rate sensitivity
- The Power BI dashboard built on those feeds
- A guide for connecting the model outputs to the Power BI file
- A model card covering method, assumptions and validation

*This folder is a write-up only. The forecasting script, its outputs and the model card belong to the client engagement and are not published, and the CMHC source workbook is not shared for data-sharing reasons.*
