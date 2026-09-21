"""Generate a SYNTHETIC, deliberately messy property-sales dataset for Gauteng.

Important: the data is simulated. Suburb price levels are illustrative
assumptions, NOT real market figures. To use real data, replace
data/raw/listings_raw.csv with your own file (see README, "Using real data").

The mess is intentional so the cleaning step has real work to do:
inconsistent suburb spellings, prices stored as text, missing values,
impossible floor sizes, duplicate rows, and dates in the wrong order.
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_LISTINGS = 6000
# Listings run Jan 2023 - Apr 2026; sales close within 120 days, so no sale date is in the future.
START, END = pd.Timestamp("2023-01-01"), pd.Timestamp("2026-04-30")

# suburb: (illustrative base R/m2, demand 0-1, sampling weight)
SUBURBS = {
    "Waterkloof": (24000, 0.75, 9),
    "Waterkloof Ridge": (26000, 0.70, 6),
    "Groenkloof": (19000, 0.60, 7),
    "Brooklyn": (21000, 0.80, 9),
    "Menlo Park": (20000, 0.75, 8),
    "Lynnwood": (19500, 0.70, 9),
    "Faerie Glen": (16000, 0.55, 8),
    "Irene": (17500, 0.50, 7),
    "Centurion": (17000, 0.65, 12),
    "Rooihuiskraal": (14000, 0.45, 6),
    "Bryanston": (26000, 0.70, 9),
    "Sandton": (30000, 0.60, 10),
}
DIRTY_ALIASES = {"Waterkloof Ridge": "Waterkloof Rdg", "Menlo Park": "Menlo Pk", "Faerie Glen": "Faerie Glen Ext"}

TYPES = {  # type: (share, median m2, sigma, price multiplier)
    "House": (0.55, 240, 0.35, 1.00),
    "Apartment": (0.33, 85, 0.30, 0.92),
    "Townhouse": (0.12, 160, 0.28, 0.96),
}


def money_text(value: float, rng: np.random.Generator) -> str:
    """Format a price the way it might arrive from different sources."""
    v = int(round(value, -3))
    style = rng.integers(0, 4)
    if style == 0:
        return f"R {v:,}".replace(",", " ")
    if style == 1:
        return f"R{v:,}"
    if style == 2:
        return str(v)
    return f"R {v:,}.00".replace(",", " ")


def main() -> None:
    rng = np.random.default_rng(SEED)
    names = list(SUBURBS)
    weights = np.array([SUBURBS[s][2] for s in names], dtype=float)
    weights /= weights.sum()

    suburb = rng.choice(names, N_LISTINGS, p=weights)
    ptype = rng.choice(list(TYPES), N_LISTINGS, p=[t[0] for t in TYPES.values()])

    span_days = (END - START).days
    list_date = START + pd.to_timedelta(rng.integers(0, span_days, N_LISTINGS), unit="D")

    floor = np.array([rng.lognormal(np.log(TYPES[t][1]), TYPES[t][2]) for t in ptype]).round()
    floor = np.clip(floor, 30, 900)
    bedrooms = np.clip(np.round(floor / 70 + rng.normal(0, 0.6, N_LISTINGS)), 1, 6).astype(float)

    base = np.array([SUBURBS[s][0] for s in suburb], dtype=float)
    demand = np.array([SUBURBS[s][1] for s in suburb], dtype=float)
    mult = np.array([TYPES[t][3] for t in ptype], dtype=float)

    months_in = (list_date - START).days.to_numpy() / 30.4
    growth = 1 + 0.006 * months_in                      # ~0.6% per month drift
    season = 1 + 0.02 * np.sin((list_date.month.to_numpy() - 3) / 12 * 2 * np.pi)
    noise = rng.lognormal(0, 0.10, N_LISTINGS)
    list_price = floor * base * mult * growth * season * noise

    dom = rng.gamma(shape=3.0, scale=(70 - 45 * demand) / 3.0)
    dom = np.clip(np.round(dom), 3, 120).astype(int)
    discount = np.clip(rng.normal(0.06 - 0.05 * demand, 0.03), 0, 0.25)
    sold_price = list_price * (1 - discount)
    sold_date = list_date + pd.to_timedelta(dom, unit="D")

    df = pd.DataFrame({
        "listing_id": [f"L{100000 + i}" for i in range(N_LISTINGS)],
        "suburb": suburb,
        "property_type": ptype,
        "bedrooms": bedrooms,
        "floor_size_m2": floor,
        "list_date": list_date.strftime("%Y-%m-%d"),
        "sold_date": sold_date.strftime("%Y-%m-%d"),
        "list_price": [money_text(p, rng) for p in list_price],
        "sold_price": [money_text(p, rng) for p in sold_price],
        "status": "Sold",
    })

    # --- inject realistic mess -------------------------------------------
    withdrawn = rng.random(N_LISTINGS) < 0.08
    df.loc[withdrawn, ["sold_date", "sold_price"]] = np.nan
    df.loc[withdrawn, "status"] = "Withdrawn"

    dirty = rng.random(N_LISTINGS) < 0.15
    for i in np.flatnonzero(dirty):
        s = df.at[i, "suburb"]
        choice = rng.integers(0, 4)
        if choice == 0:
            df.at[i, "suburb"] = s.upper()
        elif choice == 1:
            df.at[i, "suburb"] = f"  {s.lower()} "
        elif choice == 2 and s in DIRTY_ALIASES:
            df.at[i, "suburb"] = DIRTY_ALIASES[s]
        else:
            df.at[i, "suburb"] = s.replace(" ", "  ")

    df.loc[rng.random(N_LISTINGS) < 0.04, "bedrooms"] = np.nan
    df.loc[rng.random(N_LISTINGS) < 0.03, "floor_size_m2"] = np.nan
    bad = rng.random(N_LISTINGS) < 0.004
    df.loc[bad, "floor_size_m2"] = rng.choice([0, 9, 5400, 12000], bad.sum())

    swap = (rng.random(N_LISTINGS) < 0.003) & (df["status"] == "Sold")
    df.loc[swap, "sold_date"] = "2023-01-01"           # sold before it was listed

    dupes = df.sample(frac=0.02, random_state=SEED)
    df = pd.concat([df, dupes], ignore_index=True).sample(frac=1, random_state=SEED).reset_index(drop=True)

    out = Path(__file__).resolve().parents[1] / "data" / "raw" / "listings_raw.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Wrote {len(df):,} raw rows to {out}")


if __name__ == "__main__":
    main()
