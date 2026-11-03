"""CSV-to-Excel presentation stage. No SparkSession or database writes required."""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import logging
import math
import os
from pathlib import Path
import tempfile
from openpyxl import Workbook, load_workbook
from openpyxl.chart import BarChart, DoughnutChart, ScatterChart, Reference, Series
from openpyxl.chart.series import DataPoint
from openpyxl.chart.text import RichText
from openpyxl.drawing.text import Paragraph, ParagraphProperties, CharacterProperties
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.formatting.rule import FormulaRule
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.utils import get_column_letter as letter

LOGGER=logging.getLogger('uddp')
FILES={'mart':'mart_district_pension_outreach.csv','ml':'ml_district_features.csv','match':'district_match_report.csv'}
SHEETS=['Executive Dashboard','Pension Outreach Mart','ML District Features','District Matching Report','District Comparison','Dashboard Guide','District Analysis']
COLORS={'High':'F4CCCC','Medium':'FFF2CC','Low':'D9EAD3'}
NAVY='17365D';BLUE='247BA0';PALE='F3F6FA'
COUNTS=['old_age_estimated_beneficiaries','widow_estimated_beneficiaries','disability_estimated_beneficiaries']


def category(value: str) -> str:
    return value.strip().title()


def read_csv(path: Path) -> tuple[list[str],list[dict]]:
    if not path.is_file():raise FileNotFoundError(f'Dashboard input missing: {path}')
    with path.open(encoding='utf-8-sig',newline='') as handle:
        reader=csv.DictReader(handle)
        headers=reader.fieldnames or []
        if not headers or len(set(headers))!=len(headers):raise ValueError(f'Invalid/duplicate CSV headers: {path}')
        rows=list(reader)
    if not rows or any(None in r or None in r.values() for r in rows):raise ValueError(f'Empty/malformed dashboard CSV: {path}')
    return headers,rows


def inspect_inputs(folder: Path) -> dict:
    data={k:read_csv(folder/v) for k,v in FILES.items()}
    required={'mart':['district_code','district_name','population','priority_rank','priority_category','pension_outreach_priority_score',*COUNTS],
              'ml':['district_code'],'match':['district_code','source_name','status']}
    for k,cols in required.items():
        absent=set(cols)-set(data[k][0])
        if absent:raise ValueError(f'{k} missing dashboard columns: {sorted(absent)}')
    mart=data['mart'][1];ml=data['ml'][1];matches=data['match'][1]
    codes=[r['district_code'] for r in mart]
    if len(codes)!=24 or len(set(codes))!=24:raise ValueError('Dashboard requires 24 unique Gold districts')
    if len({r['district_name'].strip().casefold() for r in mart})!=24:raise ValueError('Duplicate/blank district name')
    if any(not r['district_name'].strip() or not r['district_code'].isdigit() for r in mart):raise ValueError('Missing/invalid district identity')
    for key in ['mart','ml']:
        for r in data[key][1]:
            for col,v in r.items():
                if col in {'district_code','district_name','priority_category','score_version'} or v=='':continue
                try:number=float(v)
                except ValueError as exc:raise ValueError(f'Invalid numeric {key}.{col}: {v}') from exc
                if not math.isfinite(number):raise ValueError(f'Nonfinite {key}.{col}')
    if len(ml)!=24 or len({r['district_code'] for r in ml})!=24:raise ValueError('Dashboard requires 24 unique ML districts')
    by_code={r['district_code']:r for r in mart};issues=[]
    for r in mart:
        if category(r['priority_category']) not in COLORS:raise ValueError('Unknown Gold priority category')
        if not 0<=float(r['pension_outreach_priority_score'])<=100:raise ValueError('Invalid priority score')
        if float(r['population'])<=0 or any(float(r[c])<0 for c in COUNTS):raise ValueError('Invalid population/pension count')
    if sorted(int(r['priority_rank']) for r in mart)!=list(range(1,25)):raise ValueError('Priority ranks must be 1 through 24')
    ranked=sorted(mart,key=lambda r:(-float(r['pension_outreach_priority_score']),r['district_code']))
    if [int(r['priority_rank']) for r in ranked]!=list(range(1,25)):raise ValueError('Priority ranks differ from Gold score ordering')
    for r in ml:
        g=by_code.get(r['district_code'])
        if g is None:issues.append(f'ML district {r["district_code"]} is absent from Gold; category Unknown')
        elif 'priority_category' in r and category(r['priority_category'])!=category(g['priority_category']):raise ValueError('ML/Gold category mismatch')
        elif 'high_priority' in r and int(r['high_priority'])!=int(category(g['priority_category'])=='High'):raise ValueError('ML target/category mismatch')
        if g and 'pension_outreach_priority_score' in r and abs(float(r['pension_outreach_priority_score'])-float(g['pension_outreach_priority_score']))>1e-7:raise ValueError('ML/Gold score mismatch')
    seen=set();sources={'demographics','housing','pensions'};status={}
    for r in matches:
        key=(r['district_code'],r['source_name'])
        if key in seen:raise ValueError('Duplicate matching district/source key')
        seen.add(key);status[key]=r['status'].strip().lower()
        if r['district_code'] not in by_code:issues.append(f'Unexpected matching district {r["district_code"]}')
        if r['source_name'] not in sources:issues.append(f'Unexpected source {r["source_name"]}')
    matched=sum(all(status.get((c,s))=='matched' for s in sources) for c in codes)
    missing=[f'{c}/{s}' for c in codes for s in sorted(sources) if (c,s) not in status]
    issues += ['Missing source information: '+x for x in missing]
    issues += [f'Matching status {r["district_code"]}/{r["source_name"]}: {r["status"]}' for r in matches if r['status'].strip().lower()!='matched']
    return dict(data=data,ranked=ranked,issues=issues,matched=matched,unmatched=24-matched,
                record_matched=sum(r['status'].strip().lower()=='matched' for r in matches),missing=missing)


def excel_value(col: str,value: str):
    if value=='':return None
    if col in {'district_code','district_name','priority_category','score_version','source_name','status'}:return value
    try:
        n=float(value)
        return int(n) if n.is_integer() and abs(n)<2**53 else n
    except ValueError:return value


def source_sheet(wb, name, headers, rows, table_name, priority=False):
    ws=wb.create_sheet(name);ws.append(headers)
    for row in rows:
        ws.append([excel_value(c,row[c]) for c in headers])
    ws.freeze_panes='C2';ws.sheet_view.showGridLines=False
    tab=Table(displayName=table_name,ref=f'A1:{letter(len(headers))}{len(rows)+1}')
    tab.tableStyleInfo=TableStyleInfo(name='TableStyleMedium2',showRowStripes=False)
    ws.add_table(tab);ws.auto_filter.ref=tab.ref
    for i,c in enumerate(headers,1):
        ws.column_dimensions[letter(i)].width=24 if c!='district_name' else 25
        ws.cell(1,i).alignment=Alignment(wrap_text=True,vertical='center')
        ws.cell(1,i).font=Font(bold=True,color='FFFFFF',name='Calibri')
        ws.cell(1,i).fill=PatternFill('solid',fgColor=NAVY)
        for j in range(2,len(rows)+2):
            cell=ws.cell(j,i);cell.font=Font(name='Calibri',size=11)
            cell.number_format='@' if c=='district_code' else ('0.0%' if c.endswith('_share') or c=='work_participation_rate' else ('0.00' if ('score' in c and c!='score_version') or 'per_1000' in c or c.endswith('_pct') or c=='population_per_household' else '#,##0'))
            if cell.data_type=='f':cell.data_type='s' # Imported text must never execute as a formula.
    ws.row_dimensions[1].height=48
    if priority:
        col=letter(headers.index('priority_category')+1)
        for label,color in COLORS.items():
            ws.conditional_formatting.add(f'A2:{letter(len(headers))}{len(rows)+1}',FormulaRule(formula=[f'UPPER(TRIM(${col}2))="{label.upper()}"'],fill=PatternFill('solid',fgColor=color),stopIfTrue=True))
    return ws


def generate_dashboard(folder: Path,output: Path,run_id: str='standalone') -> dict:
    """Validate three CSVs and atomically replace one native Excel workbook."""
    folder=Path(folder);output=Path(output);profile=inspect_inputs(folder)
    headers,mart=profile['data']['mart'];ml_headers,ml=profile['data']['ml'];mh,matches=profile['data']['match']
    ml_headers=list(ml_headers);ml=[dict(r) for r in ml]
    if 'priority_category' not in ml_headers:
        ml_headers.append('priority_category');lookup={r['district_code']:r['priority_category'] for r in mart}
        for r in ml:r['priority_category']=lookup.get(r['district_code'],'Unknown')
    wb=Workbook();dash=wb.active;dash.title=SHEETS[0]
    gold=source_sheet(wb,SHEETS[1],headers,mart,'OutreachMart',True)
    source_sheet(wb,SHEETS[2],ml_headers,ml,'MLFeatures',True)
    matching=source_sheet(wb,SHEETS[3],mh,matches,'DistrictMatches')
    compare=wb.create_sheet(SHEETS[4]);guide=wb.create_sheet(SHEETS[5])
    wb.calculation=CalcProperties(calcId=191029,fullCalcOnLoad=True)
    for ws in [dash,compare,guide]:
        ws.sheet_view.showGridLines=False;ws.sheet_properties.pageSetUpPr.fitToPage=True
        ws.freeze_panes='A5';ws.sheet_properties.outlinePr.summaryRight=False
        for col in range(1,13):ws.column_dimensions[letter(col)].width=13
    def band(ws,row,text):
        ws.merge_cells(start_row=row,start_column=1,end_row=row,end_column=12)
        cell=ws.cell(row,1,text);cell.fill=PatternFill('solid',fgColor=NAVY);cell.font=Font(name='Calibri',size=18 if row==1 else 12,bold=True,color='FFFFFF');cell.alignment=Alignment(vertical='center',wrap_text=True);ws.row_dimensions[row].height=36
    def note(ws,row,text):
        ws.merge_cells(start_row=row,start_column=1,end_row=row,end_column=12);ws.cell(row,1,text).alignment=Alignment(wrap_text=True,vertical='center');ws.row_dimensions[row].height=32
    def rng(col):return f"'Pension Outreach Mart'!${letter(headers.index(col)+1)}$2:${letter(headers.index(col)+1)}$25"
    band(dash,1,'Jharkhand Mini-UDDP | District Pension Outreach Dashboard')
    note(dash,2,'SUPPLIED ESTIMATES | Census 2011 | Pension reference year unknown | Not eligible-person coverage')
    note(dash,3,f'Generated {datetime.now(timezone.utc).isoformat(timespec="seconds")} UTC | Run {run_id} | Scores and categories copied from Gold')
    for i,name in enumerate(SHEETS[1:]):
        cell=dash.cell(4,1+i*2,name);cell.hyperlink=f"#'{name}'!A1";cell.font=Font(color=BLUE,underline='single',size=10)
    kpis=[('Total districts',f'COUNTA({rng("district_code")})','#,##0'),('High priority',f'SUMPRODUCT(--(UPPER(TRIM({rng("priority_category")}))="HIGH"))','0'),('Medium priority',f'SUMPRODUCT(--(UPPER(TRIM({rng("priority_category")}))="MEDIUM"))','0'),('Low priority',f'SUMPRODUCT(--(UPPER(TRIM({rng("priority_category")}))="LOW"))','0'),
          ('Old age estimated',f'SUM({rng(COUNTS[0])})','#,##0'),('Widow estimated',f'SUM({rng(COUNTS[1])})','#,##0'),('Disability estimated',f'SUM({rng(COUNTS[2])})','#,##0'),('All scheme entries',f'SUM({rng(COUNTS[0])},{rng(COUNTS[1])},{rng(COUNTS[2])})','#,##0'),
          ('Average priority score',f'AVERAGE({rng("pension_outreach_priority_score")})','0.00'),('Matched districts','COUNTIF(\'District Matching Report\'!$F$2:$F$25,"Matched")','0'),('Unmatched districts','24-A12','0'),('District match success','IFERROR(E12/A6,0)','0.0%')]
    # Card positions: 4 cards per band; label row then value row.
    for i,(label,formula,fmt) in enumerate(kpis):
        row=5+(i//4)*3;col=1+(i%4)*3
        if i==10:formula='A6-E12'
        if i==11:formula='IFERROR(E12/A6,0)'
        # matched card is column D (not E) because each card spans 3 columns.
        if i==10:formula='A6-D12'
        if i==11:formula='IFERROR(D12/A6,0)'
        dash.merge_cells(start_row=row,start_column=col,end_row=row,end_column=col+2)
        dash.merge_cells(start_row=row+1,start_column=col,end_row=row+1,end_column=col+2)
        dash.cell(row,col,label).font=Font(bold=True,color=NAVY,size=11)
        val=dash.cell(row+1,col,'='+formula);val.font=Font(bold=True,size=23,color=NAVY);val.number_format=fmt;val.fill=PatternFill('solid',fgColor=PALE);dash.row_dimensions[row+1].height=33
    band(dash,15,'DISTRICTS REQUIRING HIGH PRIORITY')
    high=[r for r in profile['ranked'] if category(r['priority_category'])=='High']
    view=['district_name','district_code','priority_rank','pension_outreach_priority_score','priority_category','population',*COUNTS,'estimated_old_age_per_1000_population','estimated_widow_per_1000_population']
    labels=['District','Code','Rank','Score','Priority','Population','Old age est.','Widow est.','Disability est.','Old age /1k','Widow /1k','All entries est.']
    for c,label in enumerate(labels,1):dash.cell(16,c,label).font=Font(bold=True,color=NAVY);dash.cell(16,c).alignment=Alignment(wrap_text=True)
    dash.row_dimensions[16].height=32
    positions={r['district_code']:i+2 for i,r in enumerate(mart)}
    for row,r in enumerate(high,17):
        for c,col in enumerate(view,1):
            dash.cell(row,c,f"='Pension Outreach Mart'!{letter(headers.index(col)+1)}{positions[r['district_code']]}").number_format='0.00' if c in [4,10,11] else '#,##0'
            dash.cell(row,c).fill=PatternFill('solid',fgColor=COLORS['High'])
        dash.cell(row,12,f'SUM(G{row}:I{row})').value='='+f'SUM(G{row}:I{row})';dash.cell(row,12).number_format='#,##0';dash.cell(row,12).fill=PatternFill('solid',fgColor=COLORS['High'])
    leaders=' | '.join(f'{label}: '+next((r['district_name'] for r in profile['ranked'] if category(r['priority_category'])==label),'None') for label in COLORS)
    note(dash,25,'Highest score within category | '+leaders)
    note(dash,26,'Rates = estimated entries per 1,000 total residents. All-scheme totals may overlap across people; they are not unique beneficiaries.')
    # A district/source matrix is derived only from supplied matching records.
    for c,label in enumerate(['District code','Demographics','Housing','Pensions','District status'],4):matching.cell(1,c,label).font=Font(bold=True,color=NAVY)
    for row,g in enumerate(mart,2):
        matching.cell(row,4,g['district_code']).number_format='@'
        for col,source in enumerate(['demographics','housing','pensions'],5):
            matching.cell(row,col,f'=IF(COUNTIFS($A$2:$A${len(matches)+1},D{row},$B$2:$B${len(matches)+1},"{source}",$C$2:$C${len(matches)+1},"matched")=1,"Matched","Missing or unmatched")')
        matching.cell(row,8,f'=IF(COUNTIF(E{row}:G{row},"Matched")=3,"Matched","Unmatched")')
    # Correct KPI to the full three-source district outcome in column H.
    dash['D12']="=COUNTIF('District Matching Report'!$H$2:$H$25,\"Matched\")"
    dash['D12'].number_format='0';dash['D12'].font=Font(bold=True,size=23,color=NAVY)
    # Matching status formatting is semantic blue/orange; no priority rules here.
    matching.conditional_formatting.add(f'C2:C{len(matches)+1}',FormulaRule(formula=['LOWER(TRIM(C2))<>"matched"'],fill=PatternFill('solid',fgColor='FFE0B2')))
    for c in range(4,9):matching.column_dimensions[letter(c)].width=25
    # Chart source helpers on the landing page; not extra worksheets.
    for i,label in enumerate(['High','Medium','Low'],2):dash.cell(i,15,label);dash.cell(i,16,f'=SUMPRODUCT(--(UPPER(TRIM({rng("priority_category")}))=UPPER(O{i})))')
    for i,g in enumerate(profile['ranked'],8):
        gr=positions[g['district_code']];dash.cell(i,15,f"='Pension Outreach Mart'!{letter(headers.index('district_name')+1)}{gr}")
        for c,col in enumerate(['pension_outreach_priority_score',*COUNTS,'population','estimated_old_age_per_1000_population','estimated_widow_per_1000_population'],16):dash.cell(i,c,f"='Pension Outreach Mart'!{letter(headers.index(col)+1)}{gr}")
    for i,(label,formula) in enumerate([('Matched',f'COUNTIF(\'District Matching Report\'!$C$2:$C${len(matches)+1},"matched")'),('Unmatched',f'COUNTA(\'District Matching Report\'!$C$2:$C${len(matches)+1})-P35')],35):dash.cell(i,15,label);dash.cell(i,16,'='+formula)
    def chart(kind,title,anchor,data_min,data_max,col_min,col_max,cat_min=8,cat_max=31):
        ch=kind();ch.title=title;ch.width=14;ch.height=8;ch.style=10
        ch.add_data(Reference(dash,min_col=col_min,max_col=col_max,min_row=data_min,max_row=data_max),titles_from_data=False)
        ch.set_categories(Reference(dash,min_col=15,min_row=cat_min,max_row=cat_max));dash.add_chart(ch,anchor);return ch
    pie=chart(DoughnutChart,'District priority distribution','A28',2,4,16,16,2,4)
    for i,color in enumerate(['C0504D','FFC000','70AD47']):dp=DataPoint(idx=i);dp.graphicalProperties.solidFill=color;pie.series[0].data_points.append(dp)
    bar=chart(BarChart,'Top 10 priority districts','G28',8,17,16,16,8,17);bar.type='bar';bar.height=9;bar.x_axis.txPr=RichText(p=[Paragraph(pPr=ParagraphProperties(defRPr=CharacterProperties(sz=900)))]) ;bar.x_axis.tickLblSkip=1;bar.x_axis.scaling.orientation='maxMin';bar.y_axis.crosses='max';bar.y_axis.title='Priority score';bar.legend=None
    stack=chart(BarChart,'Estimated scheme entries by district','A45',8,31,17,19);stack.grouping='stacked';stack.overlap=100;stack.y_axis.title='Estimated entries';stack.x_axis.title='District';
    from openpyxl.chart.series import SeriesLabel
    for series,title in zip(stack.series,['Old age','Widow','Disability']):series.tx=SeriesLabel(strRef=None,v=title)
    scatter=ScatterChart();scatter.title='Priority score vs population';scatter.width=14;scatter.height=8;scatter.x_axis.title='Population';scatter.y_axis.title='Priority score';scatter.series.append(Series(Reference(dash,min_col=16,min_row=8,max_row=31),Reference(dash,min_col=20,min_row=8,max_row=31),title='Districts'));scatter.series[0].marker.symbol='circle';scatter.series[0].marker.size=5;scatter.series[0].marker.graphicalProperties.solidFill=BLUE;scatter.series[0].marker.graphicalProperties.line.solidFill=BLUE;scatter.series[0].graphicalProperties.line.noFill=True;scatter.series[0].smooth=False;dash.add_chart(scatter,'G45')
    matchchart=chart(BarChart,'Source matching records','A62',35,36,16,16,35,36);matchchart.y_axis.title='Source records';matchchart.legend=None
    outreach=chart(BarChart,'Estimated pension rates by district','G62',8,31,21,22);outreach.y_axis.title='Estimated entries / 1,000 residents'
    for series,title in zip(outreach.series,['Old age','Widow']):series.tx=SeriesLabel(v=title)
    dash.column_dimensions.group('N','W',hidden=True)
    for ch in dash._charts:ch.visible_cells_only=False
    dash.print_options.horizontalCentered=True;dash.print_area='A1:L78';dash.sheet_properties.pageSetUpPr.fitToPage=True;dash.page_setup.orientation='landscape';dash.page_setup.paperSize=dash.PAPERSIZE_A3;dash.page_setup.fitToWidth=1;dash.page_setup.fitToHeight=0
    from openpyxl.worksheet.pagebreak import Break
    dash.row_breaks.append(Break(id=27));dash.row_breaks.append(Break(id=61))
    # District comparison selectors use native validation and exact-match INDEX/MATCH.
    band(compare,1,'District comparison | select two districts')
    names=[r['district_name'] for r in mart];compare['B3']='District A';compare['H3']='District B'
    compare['C3']=profile['ranked'][0]['district_name'];compare['I3']=profile['ranked'][1]['district_name']
    wb.defined_names.add(DefinedName('DistrictNames',attr_text=rng('district_name')))
    validation=DataValidation(type='list',formula1='DistrictNames',allow_blank=False);validation.errorTitle='Select a district';validation.error='Choose a name from the list.';validation.showErrorMessage=True;compare.add_data_validation(validation);validation.add(compare['C3']);validation.add(compare['I3'])
    metrics=[('Population','population'),('Priority score','pension_outreach_priority_score'),('Priority rank','priority_rank'),('Priority category','priority_category'),('Old age estimates',COUNTS[0]),('Widow estimates',COUNTS[1]),('Disability estimates',COUNTS[2]),('Old age per 1,000 population','estimated_old_age_per_1000_population'),('Widow per 1,000 population','estimated_widow_per_1000_population'),('Crude literacy share','crude_literacy_share'),('Dilapidated housing percent','dilapidated_pct'),('Open sanitation percent','open_defecation_pct'),('Households','total_households')]
    compare['A5']='Indicator';compare['D5']='District A';compare['H5']='District B'
    for row,(label,col) in enumerate(metrics,6):
        compare.merge_cells(start_row=row,start_column=1,end_row=row,end_column=3);compare.cell(row,1,label).alignment=Alignment(wrap_text=True);compare.row_dimensions[row].height=30
        for c,selector in [(4,'C3'),(8,'I3')]:
            compare.cell(row,c,f'=IFERROR(INDEX({rng(col)},MATCH(${selector[0]}$3,{rng("district_name")},0)),"Unavailable")');compare.cell(row,c).number_format='0.0%' if col.endswith('_share') else '#,##0.00'
    note(compare,20,'Use C3 and I3 dropdowns. Scores, ranks and categories are imported, never recalculated using new thresholds. Housing percentage values remain percentage points.')
    bc=BarChart();bc.title='Selected districts | priority score';bc.add_data(Reference(compare,min_col=4,max_col=8,min_row=7,max_row=7),from_rows=False);bc.width=20;bc.height=9
    # Only the two chosen score cells should become chart series.
    bc.series=[]
    for col,title in [(4,'District A'),(8,'District B')]:bc.add_data(Reference(compare,min_col=col,min_row=7,max_row=7));bc.series[-1].tx=SeriesLabel(v=title)
    compare.add_chart(bc,'A23')
    band(guide,1,'Dashboard guide and interpretation')
    notes=[('How to use','Executive Dashboard highlights current priorities. Filter or sort the Excel Tables in the mart and ML sheets. High/Medium/Low full-row rules are applied only there. District Comparison dropdowns change its formulas and score chart.'),('Refresh','Run the main pipeline to regenerate from its new successful CSVs, or use python -m src.excel_dashboard --work-dir runtime. This is a generated snapshot, not a live CSV connection. Changes to raw table scores do not rebuild the preselected High list or ranked chart helpers; rerun the generator.'),('Priority meaning','Existing Gold scores and categories are preserved. The rule ranks districts into approximately thirds, with deterministic district-code tie breaks. This is an explainable heuristic, not verified unmet eligibility.'),('Estimates and units','Pension counts are supplied estimates, not independently verified district observations. All-scheme totals sum scheme entries; people may overlap. Per-population rates do not measure eligible-person coverage.'),('Sources and missing values','Census indicators are historical 2011 values. Pension reference year/allocation method are unknown. Blank CSV fields remain blank. Elderly share and eligible coverage are unavailable. Housing total 100 is a percentage base; Census Households supplies counts.'),('Matching metric','A district is successfully matched only when demographics, housing and pensions all have exactly one matched record. Success rate = matched Gold districts / total Gold districts. The matching chart counts source records instead. Missing source pairs are reported below.'),('Formula calculation','openpyxl writes native Excel formulas but does not evaluate them. Excel calculates on opening; no macros, external APIs or Excel installation are needed to generate the file. A noncalculating viewer may initially show blank formula cells.'),('Not implemented','No slicers, pivot charts, VBA or map is claimed. Tables, filters, dropdowns, formulas and standard editable charts are implemented.'),('ML category provenance','Existing ML priority_category is used. If absent, it is derived only in this workbook by exact district-code lookup to Gold. Unmatched ML codes receive Unknown and are reported.'),('Input files',str(folder)),('Run ID',run_id),('Generation time UTC',datetime.now(timezone.utc).isoformat()),('Observed issues','; '.join(profile['issues']) or 'None: all required district/source matching records are present.')]
    row=3
    for title,text in notes:
        guide.merge_cells(start_row=row,start_column=1,end_row=row,end_column=12);guide.cell(row,1,title).font=Font(bold=True,color=NAVY,size=12)
        note(guide,row+1,text);guide.row_dimensions[row+1].height=48;row+=3
    guide.cell(row,1,'Source filename');guide.cell(row,5,'SHA-256')
    for i,n in enumerate(FILES.values(),row+1):
        guide.merge_cells(start_row=i,start_column=1,end_row=i,end_column=4);guide.cell(i,1,n).alignment=Alignment(wrap_text=True)
        guide.merge_cells(start_row=i,start_column=5,end_row=i,end_column=12);guide.cell(i,5,hashlib.sha256((folder/n).read_bytes()).hexdigest());guide.row_dimensions[i].height=32
    from copy import copy
    for ws in wb:
        for row_cells in ws:
            for cell in row_cells:
                font=copy(cell.font);font.name='Calibri';cell.font=font
        ws.sheet_view.zoomScale=80
        if ws!=dash:ws.cell(ws.max_row+3,1,'Back to dashboard').hyperlink="#'Executive Dashboard'!A1"
    from .dashboard_design import apply_readable_design
    apply_readable_design(wb,profile,headers,mart,run_id)
    output.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(suffix='.xlsx',dir=output.parent);os.close(fd)
    try:
        wb.save(tmp)
        with open(tmp,'rb') as handle:check=load_workbook(handle);assert check.sheetnames==SHEETS
        os.replace(tmp,output)
    finally:Path(tmp).unlink(missing_ok=True)
    LOGGER.info(json.dumps(dict(task='excel_dashboard_generated',output=str(output),districts=24,matched=profile['matched'],issues=profile['issues'])))
    return dict(districts=24,matched_districts=profile['matched'],unmatched_districts=profile['unmatched'],issues=profile['issues'],source_rows={k:len(v[1]) for k,v in profile['data'].items()},estimated_totals={c:sum(int(r[c]) for r in mart) for c in COUNTS})


def main():
    root=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir',type=Path,default=root/'runtime');parser.add_argument('--input-dir',type=Path);parser.add_argument('--output',type=Path)
    args=parser.parse_args();logging.basicConfig(level=logging.INFO,format='%(message)s')
    try:
        if args.input_dir:folder=args.input_dir;run_id='standalone'
        else:
            publication=json.loads((args.work_dir/'outputs/latest_success.json').read_text());folder=args.work_dir/publication['output_path'];run_id=publication['run_id']
            if publication['status']!='SUCCEEDED':raise ValueError('Latest run is not successful')
            for name in FILES.values():
                actual=hashlib.sha256((folder/name).read_bytes()).hexdigest()
                if actual!=publication['csv_sha256'][name]:raise ValueError(f'Published CSV hash mismatch: {name}')
        result=generate_dashboard(folder,args.output or args.work_dir/'outputs/dashboard/Jharkhand_UDDP_Interactive_Dashboard.xlsx',run_id)
        print(json.dumps(result));return 0
    except Exception as exc:LOGGER.error('Excel dashboard failed: %s',exc);return 1

if __name__=='__main__':raise SystemExit(main())
