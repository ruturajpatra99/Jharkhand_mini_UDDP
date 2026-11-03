"""Workbook tests use real aggregates and explicitly mutated temporary copies."""
import csv
from pathlib import Path
import shutil
import zipfile
import pytest
from openpyxl import load_workbook
from src.excel_dashboard import generate_dashboard,inspect_inputs,FILES,SHEETS,COLORS
from .conftest import ROOT

@pytest.fixture
def inputs(tmp_path):
    for name in FILES.values():shutil.copyfile(ROOT/'outputs'/name,tmp_path/name)
    return tmp_path

def edit_csv(folder,key,change):
    p=folder/FILES[key]
    with p.open(newline='',encoding='utf-8') as f:r=csv.DictReader(f);headers=r.fieldnames;rows=list(r)
    headers,rows=change(headers,rows)
    with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=headers);w.writeheader();w.writerows(rows)

@pytest.fixture
def book(inputs):
    p=inputs/'dashboard.xlsx';summary=generate_dashboard(inputs,p)
    return p,load_workbook(p),summary

def test_workbook_structure_and_counts(book):
    p,b,s=book
    assert b.sheetnames==SHEETS
    assert s['source_rows']=={'mart':24,'ml':24,'match':72}
    assert s['matched_districts']==24 and s['unmatched_districts']==0
    assert len(b[SHEETS[0]]._charts)==2
    assert len(b['District Analysis']._charts)==4
    assert len(b[SHEETS[4]].data_validations.dataValidation)==1
    assert len(b[SHEETS[4]]._charts)==1
    with zipfile.ZipFile(p) as z:assert z.testzip() is None

def test_all_csv_values_preserved(book,inputs):
    _,b,_=book
    for key,sheet in [('mart',SHEETS[1]),('ml',SHEETS[2]),('match',SHEETS[3])]:
        with (inputs/FILES[key]).open(newline='',encoding='utf-8') as f:reader=csv.DictReader(f);headers=reader.fieldnames;rows=list(reader)
        ws=b[sheet]
        assert [c.value for c in ws[1]][:len(headers)]==headers
        for i,r in enumerate(rows,2):
            for j,col in enumerate(headers,1):
                actual=ws.cell(i,j).value
                if r[col]=='':assert actual is None
                elif col in ['district_code','district_name','priority_category','score_version','source_name','status']:assert actual==r[col]
                else:assert float(actual)==pytest.approx(float(r[col]),rel=1e-14,abs=1e-12)
        assert len(ws.tables)==1
        assert ws.freeze_panes=='C2'

@pytest.mark.parametrize('sheet,key',[(SHEETS[1],'mart'),(SHEETS[2],'ml')])
def test_entire_row_rules(book,sheet,key):
    _,b,_=book;ws=b[sheet]
    headers=[c.value for c in ws[1]]
    from openpyxl.utils import get_column_letter as L
    ranges=list(ws.conditional_formatting)
    assert len(ranges)==1 and str(ranges[0].sqref)==f'A2:{L(len(headers))}25'
    rules=ws.conditional_formatting[ranges[0]]
    for rule,(label,color) in zip(rules,COLORS.items()):
        assert rule.formula==[f'UPPER(TRIM(${L(headers.index("priority_category")+1)}2))="{label.upper()}"']
        assert rule.dxf.fill.fgColor.rgb.endswith(color)
    for name in [SHEETS[0],SHEETS[3],SHEETS[4],SHEETS[5]]:
        for rng in b[name].conditional_formatting:
            assert all('HIGH' not in ''.join(r.formula) for r in b[name].conditional_formatting[rng])

def test_reordered_priority_headers_and_case(inputs):
    def reorder(h,rows):
        for r in rows:r['priority_category']=' '+r['priority_category'].lower()+' '
        return ['priority_category']+[c for c in h if c!='priority_category'],rows
    for key in ['mart','ml']:edit_csv(inputs,key,reorder)
    p=inputs/'book.xlsx';generate_dashboard(inputs,p);b=load_workbook(p)
    for sheet in [SHEETS[1],SHEETS[2]]:
        rng=list(b[sheet].conditional_formatting)[0]
        assert '$A2' in b[sheet].conditional_formatting[rng][0].formula[0]

def test_ml_priority_fallback_and_unknown(inputs):
    def change(h,r):
        for row in r:row.pop('priority_category')
        r[0]['district_code']='999'
        return [c for c in h if c!='priority_category'],r
    edit_csv(inputs,'ml',change);p=inputs/'book.xlsx';s=generate_dashboard(inputs,p);b=load_workbook(p)
    ws=b[SHEETS[2]];assert ws.cell(2,ws.max_column).value=='Unknown'
    assert s['issues'] and 'Unknown' in s['issues'][0]

def test_matching_missing_pair_is_visible(inputs):
    edit_csv(inputs,'match',lambda h,r:(h,r[1:]));s=generate_dashboard(inputs,inputs/'b.xlsx')
    assert s['matched_districts']==23 and len(s['issues'])==1

def test_kpi_formulas_and_high_order(book):
    _,b,s=book;ws=b[SHEETS[0]]
    assert s['estimated_totals']=={'old_age_estimated_beneficiaries':993567,'widow_estimated_beneficiaries':272108,'disability_estimated_beneficiaries':31286}
    assert ws['B7'].value.startswith('=COUNTA(') and ws['E7'].value.startswith('=SUMPRODUCT(')
    assert ws['K7'].value=='=IFERROR(COUNTIF(\'District Matching Report\'!$H$2:$H$25,"Matched")/B7,0)'
    assert ws['H7'].value.startswith('=SUM(')
    assert ws['E16'].value is None # grouped headers have one clear label
    assert ws['C17'].value.endswith('7') # Godda is seventh original data row (row 7).
    for chart in ws._charts:
        for ser in chart.series:
            ref=ser.val.numRef.f if ser.val else ser.yVal.numRef.f
            assert 'Executive Dashboard' in ref

def test_atomic_rerun_and_missing_input(inputs):
    p=inputs/'book.xlsx';generate_dashboard(inputs,p);generate_dashboard(inputs,p)
    assert load_workbook(p).sheetnames==SHEETS
    before=p.read_bytes();(inputs/FILES['mart']).unlink()
    with pytest.raises(FileNotFoundError):generate_dashboard(inputs,p)
    assert p.read_bytes()==before

@pytest.mark.parametrize('key,col,val',[('mart','population','NaN'),('mart','priority_category','Invalid'),('ml','priority_category','Invalid')])
def test_invalid_inputs_fail(inputs,key,col,val):
    def change(h,r):r[0][col]=val;return h,r
    edit_csv(inputs,key,change)
    with pytest.raises(ValueError):generate_dashboard(inputs,inputs/'book.xlsx')

def test_readable_dashboard_navigation_and_comparison(book):
    _,b,_=book;ws=b['Executive Dashboard'];comparison=b['District Comparison']
    assert ws['B2'].value=='JHARKHAND | Pension Outreach'
    assert [ws.cell(6,c).value for c in [2,5,8,11]]==['DISTRICTS IN VIEW','HIGH PRIORITY','ESTIMATED SCHEME ENTRIES','DISTRICTS MATCHED']
    assert ws['H11'].hyperlink.target=="#'District Analysis'!A1"
    assert ws['F17'].number_format=='0.0'
    assert comparison['E10'].value.startswith('=IFERROR(INDEX(')
    assert comparison['E18'].number_format=='0.0%'
    assert comparison['E19'].number_format=='0.0"%"'
    assert len(b['District Analysis']._charts)+len(ws._charts)==6
