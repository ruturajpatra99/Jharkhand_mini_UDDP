"""Read-only CSV profiling. Full original columns retained in the inventory."""
from __future__ import annotations
import csv,json,re
from decimal import Decimal,InvalidOperation
from pathlib import Path
from .extract import read_csv,digest
from .load import export_rows


def inferred(values: list[str]) -> tuple[str,int]:
    nonblank=[v.strip() for v in values if v is not None and v.strip()]
    numbers=[]
    for value in nonblank:
        try:
            number=Decimal(value.replace(',',''))
            if not number.is_finite():raise InvalidOperation
            numbers.append(number)
        except InvalidOperation:pass
    if len(numbers)==len(nonblank) and nonblank:return ('integer' if all(n==int(n) for n in numbers) else 'decimal'),0
    return 'string',len(nonblank)-len(numbers)


def profile(project: Path) -> dict:
    settings=json.loads((project/'config/settings.json').read_text());summaries={};columns=[]
    keys={'demographics':('State name','District code','District name'),'housing':('State Name','District Code','District Name'),'pensions':('States/UTs','District Code','District')}
    for source,spec in settings['sources'].items():
        path=project/'data/input'/spec['filename'];rows=read_csv(path);state,code,name=keys[source]
        scoped=[r for r in rows if r[state].strip().casefold()=='jharkhand']
        summaries[source]=dict(filename=path.name,sha256=digest(path),raw_rows=len(rows),columns=len(rows[0]),jharkhand_rows=len(scoped),unique_districts=len({r[code] for r in scoped}),duplicate_rows=len(scoped)-len({tuple(r.items()) for r in scoped}),blank_cells=sum(not v.strip() for r in scoped for v in r.values()),district_names=[r[name] for r in scoped],district_codes=[r[code] for r in scoped])
        for column in rows[0]:
            vals=[r[column] for r in scoped];dtype,non_numeric=inferred(vals)
            columns.append(dict(source=source,original_column=column,inferred_jharkhand_type=dtype,blank_jharkhand=sum(not v.strip() for v in vals),unique_jharkhand=len(set(vals)),nonnumeric_values=non_numeric if dtype!='string' else 'not_applicable',sample=vals[0]))
    (project/'docs/source_profile.json').write_text(json.dumps(summaries,indent=2))
    export_rows(project/'docs/source_column_profile.csv',columns)
    return summaries

if __name__=='__main__':
    print(json.dumps(profile(Path(__file__).resolve().parents[1]),indent=2))
