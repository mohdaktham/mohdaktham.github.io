"""Download Toronto's daily shelter occupancy data and shape it into a star schema.

Source: City of Toronto Open Data, "Daily Shelter & Overnight Service Occupancy
& Capacity" (Open Government Licence - Toronto). One row per program per night.

Run:  python prepare_data.py

Writes three files to data/ that the Power BI model loads:

  fact_occupancy.csv   one row per program per night
  dim_program.csv      one row per program version (see below)
  dim_location.csv     one row per shelter location

Why a "program version": the city reclassifies programs over time. A hotel
program that opened under "COVID-19 Response" can later move to the base
shelter system. If the dimension kept only the latest label, history would be
rewritten every time a label changed. So each distinct classification of a
program gets its own row and key, with the first and last night it applied.
This keeps history the way a type 2 slowly changing dimension does.
"""

from __future__ import annotations

import io
import json
import urllib.request
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"          # downloaded files, not committed
DATA = HERE / "data"

PACKAGE = (
    "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_show"
    "?id=daily-shelter-overnight-service-occupancy-capacity"
)

# The model covers complete months only, so every month is comparable.
FIRST_NIGHT = "2021-01-01"
LAST_NIGHT = "2026-10-31"

TEXT_COLUMNS = [
    "ORGANIZATION_NAME", "SHELTER_GROUP", "LOCATION_NAME", "LOCATION_ADDRESS", "LOCATION_POSTAL_CODE",
    "LOCATION_CITY", "PROGRAM_NAME", "SECTOR", "PROGRAM_MODEL", "OVERNIGHT_SERVICE_TYPE", "PROGRAM_AREA",
    "CAPACITY_TYPE",
]

# The classification columns that define a program version.
VERSION_COLUMNS = [
    "SECTOR",
    "PROGRAM_MODEL",
    "OVERNIGHT_SERVICE_TYPE",
    "PROGRAM_AREA",
    "CAPACITY_TYPE",
]


def download() -> list[Path]:
    """Fetch every yearly CSV listed for the dataset. Skips files already present."""
    RAW.mkdir(exist_ok=True)
    with urllib.request.urlopen(PACKAGE, timeout=60) as response:
        resources = json.load(response)["result"]["resources"]
    paths = []
    for resource in resources:
        if resource["format"] != "CSV" or resource["datastore_active"]:
            continue
        path = RAW / resource["url"].rsplit("/", 1)[-1]
        if not path.exists():
            with urllib.request.urlopen(resource["url"], timeout=300) as response:
                path.write_bytes(response.read())
        paths.append(path)
    return sorted(paths)


def parse_dates(text: pd.Series) -> pd.Series:
    """The yearly files use three date formats: 21-01-01, 2023-01-01T00:00:00, 2024-01-01."""
    day = text.str.slice(0, 10)
    short = day.str.match(r"^\d{2}-\d{2}-\d{2}$")
    day = day.where(~short, "20" + day)
    return pd.to_datetime(day, format="%Y-%m-%d")


def load(paths: list[Path]) -> pd.DataFrame:
    frames = []
    for path in paths:
        frame = pd.read_csv(io.BytesIO(path.read_bytes()), dtype={"OCCUPANCY_DATE": str}, low_memory=False)
        frame["Date"] = parse_dates(frame["OCCUPANCY_DATE"])
        frames.append(frame)
    nights = pd.concat(frames, ignore_index=True)
    nights = nights[(nights["Date"] >= FIRST_NIGHT) & (nights["Date"] <= LAST_NIGHT)].copy()

    for column in TEXT_COLUMNS:
        nights[column] = nights[column].str.strip()   # "North York " and "North York" are one city
    for column in VERSION_COLUMNS + ["LOCATION_CITY"]:
        nights[column] = nights[column].fillna("Not reported")

    assert not nights.duplicated(["PROGRAM_ID", "Date"]).any(), "expected one row per program per night"
    return nights.sort_values(["Date", "PROGRAM_ID"]).reset_index(drop=True)


def latest(nights: pd.DataFrame, key: str, columns: list[str]) -> pd.DataFrame:
    """The most recent non-missing value of each column for each key."""
    ordered = nights.sort_values("Date")
    return ordered.groupby(key)[columns].last().reset_index()


def build_locations(nights: pd.DataFrame) -> pd.DataFrame:
    known = nights.dropna(subset=["LOCATION_ID"]).copy()
    known["LOCATION_ID"] = known["LOCATION_ID"].astype(int)
    locations = latest(
        known, "LOCATION_ID", ["LOCATION_NAME", "LOCATION_ADDRESS", "LOCATION_POSTAL_CODE", "LOCATION_CITY"]
    )
    locations = locations.rename(
        columns={
            "LOCATION_ID": "LocationKey",
            "LOCATION_NAME": "Location",
            "LOCATION_ADDRESS": "Address",
            "LOCATION_POSTAL_CODE": "PostalCode",
            "LOCATION_CITY": "City",
        }
    )
    locations["Location"] = locations["Location"].fillna("Unnamed location")
    # The first three characters of a postal code are its forward sortation area.
    locations["PostalArea"] = locations["PostalCode"].str.replace(" ", "").str.slice(0, 3).str.upper()
    unknown = pd.DataFrame(
        [{"LocationKey": 0, "Location": "Not reported", "City": "Not reported"}]
    )
    return pd.concat([unknown, locations], ignore_index=True)


def build_programs(nights: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """One row per program version, and the version key for every fact row."""
    versions = (
        nights.groupby(["PROGRAM_ID"] + VERSION_COLUMNS)["Date"]
        .agg(FirstNight="min", LastNight="max")
        .reset_index()
        .sort_values(["PROGRAM_ID", "FirstNight"])
        .reset_index(drop=True)
    )
    versions.insert(0, "ProgramKey", versions.index + 1)

    names = latest(nights, "PROGRAM_ID", ["PROGRAM_NAME", "ORGANIZATION_NAME", "SHELTER_GROUP"])
    programs = versions.merge(names, on="PROGRAM_ID", how="left")
    programs["PROGRAM_NAME"] = programs["PROGRAM_NAME"].fillna("Unnamed program")
    programs["SHELTER_GROUP"] = programs["SHELTER_GROUP"].fillna("Not reported")
    programs["CAPACITY_TYPE"] = programs["CAPACITY_TYPE"].str.replace(" Based Capacity", "", regex=False)
    # The classification in force on the program's most recent night.
    programs["IsCurrent"] = programs["LastNight"] == programs.groupby("PROGRAM_ID")["LastNight"].transform("max")

    keys = nights.merge(versions, on=["PROGRAM_ID"] + VERSION_COLUMNS, how="left")["ProgramKey"]
    assert keys.notna().all()

    programs = programs.rename(
        columns={
            "PROGRAM_ID": "ProgramID",
            "PROGRAM_NAME": "Program",
            "ORGANIZATION_NAME": "Organization",
            "SHELTER_GROUP": "ShelterGroup",
            "SECTOR": "Sector",
            "PROGRAM_MODEL": "ProgramModel",
            "OVERNIGHT_SERVICE_TYPE": "ServiceType",
            "PROGRAM_AREA": "ProgramArea",
            "CAPACITY_TYPE": "CapacityType",
        }
    )
    columns = [
        "ProgramKey", "ProgramID", "Program", "Organization", "ShelterGroup", "Sector", "ProgramModel",
        "ServiceType", "ProgramArea", "CapacityType", "FirstNight", "LastNight", "IsCurrent",
    ]
    return programs[columns], keys.astype(int)


def build_fact(nights: pd.DataFrame, program_keys: pd.Series) -> pd.DataFrame:
    """Beds and rooms arrive in separate columns. Each program uses one of them,
    so they fold into one set of columns; the unit lives on the program."""
    beds = nights["CAPACITY_TYPE"] == "Bed Based Capacity"
    fact = pd.DataFrame(
        {
            "Date": nights["Date"].dt.strftime("%Y-%m-%d"),
            "ProgramKey": program_keys.to_numpy(),
            "LocationKey": nights["LOCATION_ID"].fillna(0).astype(int),
            "ServiceUsers": nights["SERVICE_USER_COUNT"].astype(int),
            "Capacity": nights["CAPACITY_ACTUAL_BED"].where(beds, nights["CAPACITY_ACTUAL_ROOM"]),
            "Occupied": nights["OCCUPIED_BEDS"].where(beds, nights["OCCUPIED_ROOMS"]),
            "Unavailable": nights["UNAVAILABLE_BEDS"].where(beds, nights["UNAVAILABLE_ROOMS"]),
        }
    )
    for column in ["Capacity", "Occupied", "Unavailable"]:
        fact[column] = fact[column].astype("Int64")   # whole numbers, blank where the city left it blank
    assert fact["Capacity"].notna().all() and fact["Occupied"].notna().all()
    return fact


def main() -> None:
    nights = load(download())
    locations = build_locations(nights)
    programs, program_keys = build_programs(nights)
    fact = build_fact(nights, program_keys)

    DATA.mkdir(exist_ok=True)
    fact.to_csv(DATA / "fact_occupancy.csv", index=False, lineterminator="\n")
    programs.to_csv(DATA / "dim_program.csv", index=False, lineterminator="\n", date_format="%Y-%m-%d")
    locations.to_csv(DATA / "dim_location.csv", index=False, lineterminator="\n")

    print(f"Nights covered:    {fact['Date'].min()} to {fact['Date'].max()} ({fact['Date'].nunique():,} nights)")
    print(f"fact_occupancy:    {len(fact):,} rows")
    print(f"dim_program:       {len(programs):,} versions of {programs['ProgramID'].nunique():,} programs")
    print(f"dim_location:      {len(locations):,} rows")


if __name__ == "__main__":
    main()
