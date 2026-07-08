# Upgrading BC_Housing_Spring_Term_Update to the v13 Model

This guide wires the eight new CSVs into your existing `.pbix`. Your file currently loads `PBI_Unified_Dashboard.csv` and `PBI_Diagnostics.csv` from `C:\Users\tabos\Downloads\`, and I kept the new dashboard CSV's first eight columns identical to the old schema, so Step 1 alone fixes your existing visuals — including the broken PI_95 bounds — with zero query edits.

## Step 1 — Drop-in refresh (2 minutes)

1. Copy `PBI_Unified_Dashboard.csv` into `C:\Users\tabos\Downloads\`, replacing the old file (back the old one up first if you like).
2. Open the pbix and click **Refresh**.

Every existing visual now shows the v13 forecasts, and `PI_Lower_95` / `PI_Upper_95` contain real calibrated bounds instead of the broken values. `Winning_Model` now reads "Pooled Ridge v13" everywhere.

## Step 2 — Unlock the new columns (80/50% bands, PI method flag)

The old query hardcodes `Columns=8`, which silently drops the new columns. In **Transform Data**, open the `PBI_Unified_Dashboard` query, click the gear icon next to the **Source** step (or edit in Advanced Editor), and change:

```
Csv.Document(File.Contents("C:\Users\tabos\Downloads\PBI_Unified_Dashboard.csv"),
    [Delimiter=",", Columns=8, Encoding=1252, QuoteStyle=QuoteStyle.None])
```

to `Columns=13` (or simply delete `Columns=8,` to auto-detect). Then in the **Changed Type** step, set the four new PI columns to Decimal Number. Close & Apply.

Do the same for `PBI_Diagnostics` — the new file has 11 columns with clearer names (`OOT_WAPE`, `Naive_WAPE`, `Skill_vs_Naive_Pct`, `OOT_MASE`, `OOT_R2_vs_Naive`, `Beats_Naive`, `Intermittent_Data`, `Top_Features`). Easiest is to delete the old `Changed Type`/rename steps and re-promote headers. Any diagnostics visuals need re-pointing to the new field names.

## Step 3 — Load the six new tables

**Get Data → Text/CSV** for each of:

| File | Purpose |
|---|---|
| `PBI_Scenarios.csv` | 3-scenario forecast fan (Baseline / Downside +100bp / Upside −100bp) |
| `PBI_Backtest.csv` | Monthly Actual vs Model vs Naive for the 12-month proof window |
| `PBI_Backtest_Summary.csv` | Per-series backtest totals, WAPEs, and winner |
| `PBI_Pipeline_Indicator.csv` | Under-construction stock, conversion ratios, implied completions |
| `PBI_Rate_Sensitivity.csv` | % forecast change per +100bp, by target type and month |
| `PBI_Model_Notes.csv` | Method, assumptions, coverage — feed a documentation page |

Relationships to create (Model view): `PBI_Scenarios` and `PBI_Backtest` to your existing date/district dimensions if you use them; otherwise the tables are self-contained.

## Step 4 — New page: "Forecast & Uncertainty"

1. Line chart: X = `Date`, Y = `Completions_Value`, filter to one district via slicer (`Regional_District`, `Target_Type`).
2. Add the band: with the line chart selected, open **Analytics pane → Error bands** (Power BI Desktop ≥ Oct 2023): Upper = `PI_Upper_80`, Lower = `PI_Lower_80`, enable **Shaded area**. Add a second series or a second band for 95% if desired.
   - If your build lacks error bands: add `PI_Lower_80` and `PI_Upper_80` as extra lines, or use a layered area chart.
3. Suggested annotation (card visual, static text): *"Shaded band: 80% empirical interval — on the last 12 unseen months, 83% of actuals landed inside."*

## Step 5 — New page: "Does it actually work?" (backtest receipts)

1. Line chart from `PBI_Backtest`: X = `Date`, Y = `Actual`, `Model_Forecast`, `Naive_Forecast` (three lines), slicers for district and target.
2. Table from `PBI_Backtest_Summary` with conditional formatting on `Winner`.
3. Headline cards: **"15.1% volume-weighted error vs 27.5% naive"** and **"22 of 24 series beat the benchmark"** (from `PBI_Diagnostics`: `Beats_Naive`).

## Step 6 — New page: "Construction pipeline"

From `PBI_Pipeline_Indicator`: clustered bar of `Implied_Next_18m_Completions` vs `Model_Next_18m_Completions` by district; cards for `Months_Of_Pipeline` and `Hist_18m_Conversion_Ratio`. Talking point: the model's 18-month numbers track the physical pipeline, so the forecast is anchored to units actually under construction.

## Step 7 — Rate what-if slider

1. **Modeling → New parameter → Numeric range**: Name `Rate Change (bp)`, Min `-200`, Max `200`, Increment `25`, Default `0`. Add the slicer to the forecast page.
2. New measure (on `PBI_Unified_Dashboard`):

```DAX
Adjusted Forecast =
VAR deltaBp = SELECTEDVALUE('Rate Change (bp)'[Rate Change (bp) Value], 0) / 100
VAR sens =
    LOOKUPVALUE(
        PBI_Rate_Sensitivity[Pct_Change_Per_Plus100bp],
        PBI_Rate_Sensitivity[Target_Type], SELECTEDVALUE(PBI_Unified_Dashboard[Target_Type]),
        PBI_Rate_Sensitivity[Date],        SELECTEDVALUE(PBI_Unified_Dashboard[Date])
    )
RETURN
    SUM(PBI_Unified_Dashboard[Completions_Value]) * (1 + COALESCE(sens, 0) * deltaBp)
```

3. Add `Adjusted Forecast` as a second line on the forecast chart. Historical months have no sensitivity row, so they stay fixed while the forecast flexes with the slider. Sensitivity is ≈ −4 to −5% of completions per +100bp at 12–36 months, phased in over the first half-year (mortgage rates hit completions with a lag).

## Step 8 — Refresh workflow going forward

When new CMHC months land in `BC_Housing_CMHC_Econ_Merged.xlsx`, run:

```
python BC_Housing_Forecast_v13_production.py
```

with the workbook in the same folder. It regenerates all eight CSVs; then just refresh the pbix.

## Presentation notes

- Lead with the backtest page — it is the single most persuasive artifact.
- When showing uncertainty, say "80% band" and quote the realized 83% coverage; that honesty is a differentiator.
- For Fraser-Fort George, present annual totals only and point to the `Intermittent_Data` flag; the data there arrives in administrative bursts and no monthly model is reliable on it.
