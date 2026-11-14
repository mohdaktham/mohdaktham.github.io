"""
TTC Subway Delay Analysis (2024-2025)
Source: City of Toronto Open Data - TTC Subway Delay Data
Author: Mo Maghaireh

Analyzes 60,000+ real subway delay incidents to identify when, where,
and why delays happen, and quantifies lost service minutes by line.
Outputs 4 charts (charts/) and a findings summary (findings.txt).
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"figure.dpi": 150, "font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
C = "#c8102e"  # TTC red

# ---------- load & clean ----------
d24 = pd.read_excel("data/ttc_delays_2024.xlsx")
d25 = pd.read_csv("data/ttc_delays_2025.csv").drop(columns=["_id"])
df = pd.concat([d24, d25], ignore_index=True)
df["Date"] = pd.to_datetime(df["Date"])
df["Hour"] = pd.to_numeric(df["Time"].astype(str).str.split(":").str[0], errors="coerce")
codes = pd.read_csv("data/delay_codes.csv")[["CODE", "DESCRIPTION"]]
codes["DESCRIPTION"] = codes["DESCRIPTION"].str.replace("\u00e2\u0080\u0093", "-", regex=False).str.replace("â\u0080\u0093", "-", regex=False)
codes["DESCRIPTION"] = codes["DESCRIPTION"].apply(lambda x: x.encode("cp1252", "ignore").decode("utf-8", "ignore") if isinstance(x, str) else x).str.replace("\u2013", "-")  # ftfy_fix
df = df.merge(codes, left_on="Code", right_on="CODE", how="left")

# keep the 4 subway lines, actual delays only (Min Delay > 0)
lines = {"YU": "Line 1 (Yonge-University)", "BD": "Line 2 (Bloor-Danforth)",
         "SHP": "Line 4 (Sheppard)", "SRT": "Line 3 (SRT)"}
df["Line"] = df["Line"].astype(str).str.strip().str.upper()
raw_n = len(df)
df = df[df["Line"].isin(lines)].copy()
df["LineName"] = df["Line"].map(lines)
delays = df[df["Min Delay"] > 0].copy()

# station cleanup: strip suffixes for grouping
delays["StationClean"] = (delays["Station"].str.upper()
    .str.replace(r"\s+(STATION|BD STATION|YUS STATION|TO .*)$", "", regex=True).str.strip())

# ---------- KPIs ----------
total_incidents = len(delays)
total_min = delays["Min Delay"].sum()
kpi = {
    "records_raw": raw_n,
    "delay_incidents": total_incidents,
    "total_delay_minutes": int(total_min),
    "total_delay_days": round(total_min / 1440, 1),
    "avg_delay_min": round(delays["Min Delay"].mean(), 1),
    "median_delay_min": delays["Min Delay"].median(),
}
by_line = delays.groupby("LineName").agg(incidents=("Min Delay", "size"),
    total_min=("Min Delay", "sum"), avg_min=("Min Delay", "mean")).sort_values("total_min", ascending=False)
top_stations = delays.groupby("StationClean")["Min Delay"].agg(["size", "sum"]).sort_values("sum", ascending=False).head(10)
top_causes = delays.groupby("DESCRIPTION")["Min Delay"].agg(["size", "sum"]).sort_values("sum", ascending=False).head(10)
monthly = delays.set_index("Date").resample("MS")["Min Delay"].agg(["size", "sum"])
hourly = delays.groupby("Hour")["Min Delay"].agg(["size", "sum"]).reindex(range(24), fill_value=0)
dow = delays.groupby("Day")["Min Delay"].sum().reindex(
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])

# ---------- charts ----------
fig, ax = plt.subplots(figsize=(8, 4))
by_line["total_min"].div(60).sort_values().plot.barh(ax=ax, color=C)
ax.set_xlabel("Total delay hours (2024-2025)"); ax.set_ylabel("")
ax.set_title("Line 2 and Line 1 account for the bulk of lost service time")
plt.tight_layout(); plt.savefig("charts/delay_by_line.png"); plt.close()

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(hourly.index, hourly["size"], color=C)
ax.set_xlabel("Hour of day"); ax.set_ylabel("Delay incidents")
ax.set_title("Delays cluster around the AM and PM peaks")
ax.set_xticks(range(0, 24, 2))
plt.tight_layout(); plt.savefig("charts/delay_by_hour.png"); plt.close()

fig, ax = plt.subplots(figsize=(8, 4.5))
top_stations["sum"].div(60).sort_values().plot.barh(ax=ax, color=C)
ax.set_xlabel("Total delay hours"); ax.set_ylabel("")
ax.set_title("Top 10 stations by total delay time")
plt.tight_layout(); plt.savefig("charts/top_stations.png"); plt.close()

fig, ax = plt.subplots(figsize=(8, 4))
monthly["sum"].div(60).plot(ax=ax, color=C, marker="o", ms=3)
ax.set_ylabel("Delay hours / month"); ax.set_xlabel("")
ax.set_title("Monthly delay hours, Jan 2024 - present")
plt.tight_layout(); plt.savefig("charts/monthly_trend.png"); plt.close()

# ---------- findings ----------
with open("findings.txt", "w") as f:
    f.write("TTC SUBWAY DELAY ANALYSIS - KEY FINDINGS\n" + "=" * 45 + "\n\n")
    for k, v in kpi.items():
        f.write(f"{k}: {v}\n")
    f.write("\nBY LINE\n" + by_line.round(1).to_string())
    f.write("\n\nTOP 10 STATIONS (by delay minutes)\n" + top_stations.to_string())
    f.write("\n\nTOP 10 CAUSES (by delay minutes)\n" + top_causes.to_string())
    f.write("\n\nPEAK HOURS (top 5 by incidents)\n" + hourly["size"].nlargest(5).to_string())
    f.write("\n\nDELAY MINUTES BY DAY OF WEEK\n" + dow.to_string())
print(open("findings.txt").read())
