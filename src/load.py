"""SQLite helpers. Callers own the transaction; no implicit pandas commits."""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


def connect(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db


def insert(db: sqlite3.Connection, table: str, rows: list[dict]) -> None:
    if not rows:
        return
    # All identifiers originate in application-owned schemas, never source fields.
    columns = list(rows[0])
    db.executemany(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
                   [tuple(row[c] for c in columns) for row in rows])


def execute_script(db: sqlite3.Connection, path: Path) -> None:
    # execute(), unlike executescript(), does not pre-commit the active transaction.
    statement = ""
    for line in path.read_text().splitlines(keepends=True):
        statement += line
        if sqlite3.complete_statement(statement):
            db.execute(statement)
            statement = ""
    if statement.strip():
        raise ValueError(f"Incomplete SQL statement in {path}")


def export_rows(path: Path, rows: list[dict], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = columns or (list(rows[0]) if rows else [])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def export_table(db: sqlite3.Connection, table: str, path: Path, order: str = "district_code") -> None:
    cur = db.execute(f"SELECT * FROM {table} ORDER BY {order}")
    export_rows(path, [dict(row) for row in cur], [d[0] for d in cur.description])


def upsert(db: sqlite3.Connection, table: str, rows: list[dict], batch_size: int=100) -> None:
    """Single driver writer with identifiers validated against the deployed schema."""
    if not rows:return
    info=list(db.execute(f'PRAGMA table_info("{table}")'))
    allowed={r['name'] for r in info};columns=list(rows[0])
    if not allowed or set(columns)!=allowed:raise ValueError(f'Column contract mismatch for {table}: {set(columns)^allowed}')
    keys=[r['name'] for r in sorted(info,key=lambda x:x['pk']) if r['pk']]
    update=[c for c in columns if c not in keys]
    sql=f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)}) ON CONFLICT ({','.join(keys)}) DO UPDATE SET "+','.join(f'{c}=excluded.{c}' for c in update)
    for start in range(0,len(rows),batch_size):db.executemany(sql,[tuple(row[c] for c in columns) for row in rows[start:start+batch_size]])


def bounded_rows(frame, limit: int=1000) -> list[dict]:
    """Explicit small-mart boundary; never collect unbounded citizen data."""
    from decimal import Decimal
    rows=frame.limit(limit+1).collect()
    if len(rows)>limit:raise ValueError(f'Driver collection limit exceeded: {limit}')
    return [{k:float(v) if isinstance(v,Decimal) else v for k,v in r.asDict().items()} for r in rows]


def load_snapshot(db: sqlite3.Connection, tables: dict, batch_size: int=100, fail: bool=False) -> None:
    """Caller owns transaction. Refresh derived ranks; UPSERT stable Silver keys."""
    db.execute('DELETE FROM ml_district_features')
    db.execute('DELETE FROM mart_district_pension_outreach')
    for table,rows in tables.items():upsert(db,table,rows,batch_size)
    if fail:raise RuntimeError('Injected test failure after load')
