"""Clean the raw listings file and load it into a local DuckDB database.

Every cleaning rule is logged so the data-quality report shows exactly what
was changed and why. Nothing is silently dropped.
"""
import re
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "listings_raw.csv"
CLEAN = ROOT / "data" / "processed" / "listings_clean.csv"
DB = ROOT / "data" / "property.duckdb"
REPORT = ROOT / "outputs" / "data_quality_report.csv"

CANONICAL = [
    "Waterkloof", "Waterkloof Ridge", "Groenkloof", "Brooklyn", "Menlo Park", "Lynnwood",
    "Faerie Glen", "Irene", "Centurion", "Rooihuiskraal", "Bryanston", "Sandton",
]
ALIASES = {"waterkloof rdg": "Waterkloof Ridge", "menlo pk": "Menlo Park", "faerie glen ext": "Faerie Glen"}
LOOKUP = {name.lower(): name for name in CANONICAL} | ALIASES

MIN_M2, MAX_M2 = 15, 2000  # plausible floor-size range for a residential sale


def parse_price(value) -> float:
    """'R 2 450 000.00' / 'R2,450,000' / '2450000' -> 2450000.0"""
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    text = re.sub(r"\.\d{2}$", "", text)          # drop cents
    digits = re.sub(r"[^\d]", "", text)
    return float(digits) if digits else np.nan


def main() -> None:
    log: list[tuple[str, int, str]] = []
    df = pd.read_csv(RAW)
    log.append(("raw rows loaded", len(df), "starting point"))

    before = len(df)
    df = df.drop_duplicates(subset="listing_id", keep="first")
    log.append(("duplicate listings removed", before - len(df), "same listing_id appeared more than once"))

    cleaned = df["suburb"].str.strip().str.replace(r"\s+", " ", regex=True).str.lower().map(LOOKUP)
    log.append(("suburb names standardised", int((cleaned != df["suburb"]).sum()),
                "case, spacing and abbreviation fixes"))
    log.append(("suburb names unmapped", int(cleaned.isna().sum()), "would need a new alias; should be 0"))
    df["suburb"] = cleaned

    df["list_price_zar"] = df["list_price"].map(parse_price)
    df["sold_price_zar"] = df["sold_price"].map(parse_price)
    df = df.drop(columns=["list_price", "sold_price"])
    log.append(("price text converted to numbers", len(df), "removed 'R', spaces, commas, cents"))

    df["list_date"] = pd.to_datetime(df["list_date"])
    df["sold_date"] = pd.to_datetime(df["sold_date"])

    bad_size = (df["floor_size_m2"] < MIN_M2) | (df["floor_size_m2"] > MAX_M2)
    df.loc[bad_size, "floor_size_m2"] = np.nan
    log.append(("implausible floor sizes set to null", int(bad_size.sum()),
                f"outside {MIN_M2}-{MAX_M2} m2; row kept, price per m2 excluded"))

    log.append(("missing bedrooms left null", int(df["bedrooms"].isna().sum()),
                "not imputed: guessing would bias bedroom analysis"))
    log.append(("missing floor size left null", int(df["floor_size_m2"].isna().sum()),
                "includes the implausible values above"))

    bad_dates = (df["status"] == "Sold") & (df["sold_date"] < df["list_date"])
    df = df[~bad_dates]
    log.append(("sold-before-listed rows removed", int(bad_dates.sum()), "impossible date order"))

    df["bedrooms"] = df["bedrooms"].astype("Int64")
    df = df.sort_values("list_date").reset_index(drop=True)
    log.append(("clean rows saved", len(df), "final table"))

    CLEAN.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CLEAN, index=False)
    pd.DataFrame(log, columns=["step", "rows_affected", "note"]).to_csv(REPORT, index=False)

    con = duckdb.connect(str(DB))
    con.execute("CREATE OR REPLACE TABLE listings AS SELECT * FROM df")
    con.close()

    print("Data quality report")
    print("-" * 70)
    for step, n, note in log:
        print(f"{step:<38}{n:>8,}   {note}")


if __name__ == "__main__":
    main()
