"""Portable database demonstration without installing the sqlite3 CLI."""
import argparse
import json
from pathlib import Path
import sqlite3


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database",type=Path,nargs="?",default=Path("runtime/uddp.sqlite"))
    args=parser.parse_args()
    db=sqlite3.connect(f"{args.database.resolve().as_uri()}?mode=ro",uri=True)
    db.row_factory=sqlite3.Row
    try:
        tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        print(json.dumps({t:db.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables},indent=2))
        for row in db.execute("SELECT district_name,priority_rank,pension_outreach_priority_score,priority_category,pension_values_estimated FROM mart_district_pension_outreach ORDER BY priority_rank"):
            print(json.dumps(dict(row)))
        print("Supplied district pension estimates:")
        for row in db.execute("SELECT * FROM fact_pension_beneficiaries ORDER BY scheme"):
            print(json.dumps(dict(row)))
    finally:db.close()


if __name__=="__main__":main()
