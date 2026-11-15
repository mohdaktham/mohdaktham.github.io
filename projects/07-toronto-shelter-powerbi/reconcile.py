"""Recalculate the report's headline numbers with pandas, independently of Power BI.

The Power BI report has a "Checks" page that shows the same figures from its
DAX measures. If the two disagree, either a measure or a relationship is wrong.

Run:  python reconcile.py
Writes checks/expected_values.csv
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"


def load() -> pd.DataFrame:
    fact = pd.read_csv(DATA / "fact_occupancy.csv", parse_dates=["Date"])
    program = pd.read_csv(DATA / "dim_program.csv")
    location = pd.read_csv(DATA / "dim_location.csv")
    rows = fact.merge(program, on="ProgramKey", how="left", validate="many_to_one")
    rows = rows.merge(location, on="LocationKey", how="left", validate="many_to_one")
    assert len(rows) == len(fact)
    return rows


def people_per_night(rows: pd.DataFrame) -> float:
    return rows["ServiceUsers"].sum() / rows["Date"].nunique()


def occupancy(rows: pd.DataFrame, unit: str | None = None) -> float:
    if unit:
        rows = rows[rows["CapacityType"] == unit]
    return rows["Occupied"].sum() / rows["Capacity"].sum()


def full_share(rows: pd.DataFrame) -> float:
    return (rows["Occupied"] >= rows["Capacity"]).mean()


def main() -> None:
    rows = load()
    month = rows["Date"].dt.to_period("M")
    latest = month.max()
    this_month = rows[month == latest]
    year_earlier = rows[month == latest - 12]

    monthly = rows.groupby(month).apply(people_per_night)
    peak_month = monthly.idxmax()

    latest_people = people_per_night(this_month)
    earlier_people = people_per_night(year_earlier)

    values = [
        ("Program Nights", "all dates", f"{len(rows):,}"),
        ("Person Nights", "all dates", f"{rows['ServiceUsers'].sum():,}"),
        ("Nights Reported", "all dates", f"{rows['Date'].nunique():,}"),
        ("Programs", "all dates", f"{rows['ProgramID'].nunique():,}"),
        ("Locations", "all dates", f"{rows.loc[rows['LocationKey'] != 0, 'LocationKey'].nunique():,}"),
        ("People per Night", "all dates", f"{people_per_night(rows):,.1f}"),
        ("Occupancy %", "all dates, beds", f"{occupancy(rows, 'Bed'):.2%}"),
        ("Occupancy %", "all dates, rooms", f"{occupancy(rows, 'Room'):.2%}"),
        ("Full Program Nights %", "all dates", f"{full_share(rows):.2%}"),
        ("Latest Month", "", latest.strftime("%B %Y")),
        ("People per Night (Latest Month)", str(latest), f"{latest_people:,.1f}"),
        ("People per Night (Year Earlier)", str(latest - 12), f"{earlier_people:,.1f}"),
        ("Change vs Year Earlier %", str(latest), f"{latest_people / earlier_people - 1:.2%}"),
        ("Bed Occupancy % (Latest Month)", str(latest), f"{occupancy(this_month, 'Bed'):.2%}"),
        ("Room Occupancy % (Latest Month)", str(latest), f"{occupancy(this_month, 'Room'):.2%}"),
        ("Full Program Nights % (Latest Month)", str(latest), f"{full_share(this_month):.2%}"),
        ("Peak Month", "", peak_month.strftime("%B %Y")),
        ("People per Night (Peak Month)", str(peak_month), f"{monthly.max():,.1f}"),
        ("Change from Peak %", str(latest), f"{latest_people / monthly.max() - 1:.2%}"),
    ]
    table = pd.DataFrame(values, columns=["Measure", "Filter", "Expected"])
    (HERE / "checks").mkdir(exist_ok=True)
    table.to_csv(HERE / "checks" / "expected_values.csv", index=False, lineterminator="\n")
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
