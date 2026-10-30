"""Verify packaged aggregate outputs without starting Spark (standard library only)."""
from pathlib import Path
import csv
import hashlib
import json
import sqlite3

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    output = ROOT / 'outputs'
    publication = json.loads((output / 'publication.json').read_text())
    for name, expected in publication['csv_sha256'].items():
        path = ROOT / 'data' / name if name.startswith('silver/') else output / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
    with sqlite3.connect(output / 'uddp.sqlite') as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []
        sql = '\n'.join(line for line in (ROOT / 'sql/validations.sql').read_text().splitlines()
                        if not line.lstrip().startswith('--'))
        for query in sql.split(';'):
            if query.strip():
                assert db.execute(query).fetchall() == [], query
        for table in ['dim_district', 'fact_district_demographics', 'fact_district_housing',
                      'mart_district_pension_outreach', 'ml_district_features']:
            assert db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] == 24
        assert db.execute('SELECT COUNT(*) FROM fact_pension_beneficiaries').fetchone()[0] == 72
        totals = dict(db.execute('SELECT scheme,SUM(estimated_beneficiary_count) FROM fact_pension_beneficiaries GROUP BY scheme'))
        assert totals == {'old_age': 993567, 'widow': 272108, 'disability': 31286}
    for name in ['mart_district_pension_outreach.csv', 'ml_district_features.csv']:
        with (output / name).open(newline='', encoding='utf-8') as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == len({row['district_code'] for row in rows}) == 24
    print('PASS: packaged hashes, SQLite integrity, constraints, totals and 24-district outputs')


if __name__ == '__main__':
    main()
