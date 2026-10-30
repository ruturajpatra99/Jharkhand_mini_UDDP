"""Immutable, content-addressed ingestion of supplied CSV snapshots."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError(f"Missing/duplicate CSV headers: {path.name}")
        rows = list(reader)
        if not rows or any(None in r or None in r.values() for r in rows):
            raise ValueError(f"Empty or malformed CSV: {path.name}")
        return rows


def extract(input_dir: Path, bronze: Path, settings: dict, run_id: str) -> tuple[dict, list]:
    data, manifests = {}, []
    for source, spec in settings["sources"].items():
        source_path = input_dir / spec["filename"]
        if not source_path.is_file():
            raise FileNotFoundError(f"Required public snapshot missing: {source_path}")
        sha = digest(source_path)
        folder = bronze / source / sha
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / source_path.name
        if target.exists() and digest(target) != sha:
            raise ValueError(f"Bronze integrity failure: {target}")
        if not target.exists():
            shutil.copyfile(source_path, target)
        if digest(target) != sha:
            raise ValueError("Input changed while copying; retry with a stable snapshot")
        rows = read_csv(target)
        data[source] = rows
        manifests.append(dict(run_id=run_id, source_name=source, filename=source_path.name,
                              source_url=spec["url"], source_year=spec["source_year"],
                              sha256=sha, ingestion_timestamp=utcnow(), raw_rows=len(rows),
                              bronze_path=str(target)))
    (bronze / f"manifest_{run_id}.json").write_text(json.dumps(manifests, indent=2))
    return data, manifests
