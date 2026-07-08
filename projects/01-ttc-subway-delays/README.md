# TTC Subway Delay Analysis (2024–2025)

**Tools:** Python (pandas, NumPy, Matplotlib) · **Data:** 64,485 real delay records from [City of Toronto Open Data](https://open.toronto.ca/dataset/ttc-subway-delay-data/)

## Business question
The TTC logs every subway delay incident. Where is service time actually being lost, and what would give riders the biggest reliability improvement per dollar?

## What I did
- Combined and cleaned two years of raw delay logs (Excel + CSV extracts, ~64K records), standardized station names, and joined the TTC's delay-code lookup table to translate cryptic codes into readable causes
- Filtered to 22,814 true delay incidents across Lines 1, 2 and 4 and quantified lost service time by line, station, hour, weekday, and root cause
- Produced a reproducible analysis script that regenerates all charts and a findings summary from the raw files

## Key findings
- **126 days of service time lost** — 181,700 delay minutes over the period, averaging 8.0 min per incident (median 5)
- **Line 1 (Yonge–University) loses the most time** (100,290 min across 13,078 incidents), but Line 2 delays run longer on average (8.3 vs 7.7 min)
- **Delays peak at 8 AM and 4–5 PM** — exactly when capacity matters most; weekdays lose ~27K min each vs ~21K on Saturdays
- **The top causes are people, not equipment:** disorderly patrons (19,385 min), medical emergencies, and unauthorized track-level access dominate — supporting investment in platform safety and station staffing over pure mechanical fixes
- Eglinton, Kipling, St George and Kennedy are the highest-loss stations — all major interchange/terminal points

## Files
| File | Description |
|---|---|
| `ttc_delay_analysis.py` | Full analysis pipeline (clean → join → KPI → charts) |
| `data/` | Raw source extracts from Toronto Open Data |
| `charts/` | Generated visuals (by line, by hour, top stations, monthly trend) |
| `findings.txt` | Auto-generated summary statistics |

## Run it
```bash
pip install pandas numpy matplotlib openpyxl
python ttc_delay_analysis.py
```
