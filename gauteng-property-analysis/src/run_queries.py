"""Run every .sql file in /sql against the DuckDB database and save results as CSV.

The CSVs in /outputs are what the dashboard (Power BI / Tableau Public) connects to.
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "property.duckdb"
OUT = ROOT / "outputs"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    con = duckdb.connect(str(DB), read_only=True)
    for sql_file in sorted((ROOT / "sql").glob("*.sql")):
        result = con.execute(sql_file.read_text()).df()
        target = OUT / f"{sql_file.stem}.csv"
        result.to_csv(target, index=False)
        print(f"\n=== {sql_file.name}  ->  outputs/{target.name}  ({len(result)} rows)")
        print(result.head(8).to_string(index=False))
    con.close()


if __name__ == "__main__":
    main()
