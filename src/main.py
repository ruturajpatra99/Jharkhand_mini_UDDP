"""Run from repository root: python -m src.main [options]."""
from __future__ import annotations

import argparse
from datetime import date, timedelta
import json
import logging
import os
from pathlib import Path
import sys
from .orchestration import run


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path(os.environ.get("UDDP_INPUT_DIR", project / "data/input")))
    parser.add_argument("--work-dir", type=Path, default=Path(os.environ.get("UDDP_WORK_DIR", project / "runtime")))
    parser.add_argument("--logical-date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--settings", type=Path)
    parser.add_argument("--backfill-start", type=date.fromisoformat)
    parser.add_argument("--backfill-end", type=date.fromisoformat)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if bool(args.backfill_start) != bool(args.backfill_end):
        parser.error("Supply both backfill dates")
    start, end = (args.backfill_start, args.backfill_end) if args.backfill_start else (args.logical_date, args.logical_date)
    if end < start or (end-start).days > 31:
        parser.error("Backfill range must be ordered and no more than 32 days")
    try:
        day = start
        while day <= end:
            result = run(project, args.work_dir.resolve(), args.input_dir.resolve(), day.isoformat(), args.settings)
            print(json.dumps(result))
            day += timedelta(days=1)
        return 0
    except Exception as exc:
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
