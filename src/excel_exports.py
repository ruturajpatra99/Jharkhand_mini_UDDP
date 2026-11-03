"""Create separate colored Excel equivalents of the two analytical CSVs."""
from __future__ import annotations
import argparse
import logging
import os
from pathlib import Path
import tempfile
from openpyxl import Workbook,load_workbook
from openpyxl.comments import Comment
from .excel_dashboard import read_csv,source_sheet,category,COLORS

NAMES=['mart_district_pension_outreach','ml_district_features']
LOGGER=logging.getLogger('uddp')


def generate_excel_exports(folder: Path,output_dir: Path|None=None,*,mart_csv: Path|None=None,ml_csv: Path|None=None) -> list[Path]:
    """Preserve CSV data/ordering; dynamically color entire Excel rows by category."""
    folder=Path(folder);output_dir=Path(output_dir or folder)
    paths=[mart_csv or folder/(NAMES[0]+'.csv'),ml_csv or folder/(NAMES[1]+'.csv')]
    datasets=[read_csv(Path(p)) for p in paths]
    for headers,rows in datasets:
        if not {'district_code','priority_category'}.issubset(headers):raise ValueError('Excel export requires district_code and priority_category')
        if len({r['district_code'] for r in rows})!=len(rows):raise ValueError('Duplicate district code in Excel export')
        if any(not r['district_code'].strip() or category(r['priority_category']) not in COLORS for r in rows):raise ValueError('Missing district code or invalid priority category')
    gold,ml=datasets[0][1],datasets[1][1]
    if {r['district_code'] for r in gold}!={r['district_code'] for r in ml}:raise ValueError('Gold and ML district sets differ')
    lookup={r['district_code']:category(r['priority_category']) for r in gold}
    if any(lookup[r['district_code']]!=category(r['priority_category']) for r in ml):raise ValueError('Gold and ML priorities differ')
    output_dir.mkdir(parents=True,exist_ok=True);pending=[]
    try:
        for i,(name,(headers,rows)) in enumerate(zip(NAMES,datasets)):
            wb=Workbook();wb.remove(wb.active)
            ws=source_sheet(wb,'District Data',headers,rows,'DistrictExport'+str(i+1),priority=True)
            ws.sheet_view.zoomScale=80
            ws.cell(1,headers.index('priority_category')+1).comment=Comment('Whole-row conditional formatting: High = red, Medium = yellow, Low = green. Existing pipeline categories are preserved.','UDDP')
            ws['A1'].comment=Comment('Generated from '+Path(paths[i]).name+'. Pension values are supplied estimates. Blank fields remain blank. Original CSV remains unchanged.','UDDP')
            ws.sheet_properties.pageSetUpPr.fitToPage=True;ws.page_setup.orientation='landscape';ws.page_setup.fitToWidth=1;ws.page_setup.fitToHeight=0
            fd,tmp=tempfile.mkstemp(dir=output_dir,suffix='.xlsx');os.close(fd);pending.append((Path(tmp),output_dir/(name+'.xlsx')))
            wb.save(tmp)
            check=load_workbook(tmp);assert check['District Data'].max_row==len(rows)+1
        for tmp,target in pending:os.replace(tmp,target)
    finally:
        for tmp,_ in pending:tmp.unlink(missing_ok=True)
    LOGGER.info('Generated separate Excel exports: %s',', '.join(str(p) for _,p in pending))
    return [p for _,p in pending]


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir',type=Path,required=True);parser.add_argument('--output-dir',type=Path)
    parser.add_argument('--mart-csv',type=Path);parser.add_argument('--ml-csv',type=Path)
    args=parser.parse_args();logging.basicConfig(level=logging.INFO)
    try:
        for path in generate_excel_exports(args.input_dir,args.output_dir,mart_csv=args.mart_csv,ml_csv=args.ml_csv):print(path)
        return 0
    except Exception as exc:LOGGER.error('Excel exports failed: %s',exc);return 1

if __name__=='__main__':raise SystemExit(main())
