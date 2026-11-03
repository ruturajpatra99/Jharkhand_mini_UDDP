import csv,shutil
import pytest
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter as L
from src.excel_exports import generate_excel_exports,NAMES
from .conftest import ROOT

@pytest.fixture
def inputs(tmp_path):
    for name in NAMES:shutil.copyfile(ROOT/'outputs'/(name+'.csv'),tmp_path/(name+'.csv'))
    return tmp_path

@pytest.mark.parametrize('index',[0,1])
def test_preserved_data_and_full_row_colors(inputs,index):
    paths=generate_excel_exports(inputs);p=paths[index];ws=load_workbook(p)['District Data']
    with (inputs/(NAMES[index]+'.csv')).open(newline='',encoding='utf-8') as f:r=csv.DictReader(f);headers=r.fieldnames;rows=list(r)
    assert ws.max_row==25 and ws.max_column==len(headers)
    assert [c.value for c in ws[1]]==headers
    for i,row in enumerate(rows,2):
        for j,col in enumerate(headers,1):
            v=ws.cell(i,j).value
            if row[col]=='':assert v is None
            elif col in ['district_code','district_name','priority_category','score_version']:assert v==row[col]
            else:assert float(v)==pytest.approx(float(row[col]),rel=1e-14,abs=1e-12)
    k=list(ws.conditional_formatting)[0]
    assert str(k.sqref)==f'A2:{L(len(headers))}25'
    for rule,label,color in zip(ws.conditional_formatting[k],['HIGH','MEDIUM','LOW'],['F4CCCC','FFF2CC','D9EAD3']):
        assert rule.formula==[f'UPPER(TRIM(${L(headers.index("priority_category")+1)}2))="{label}"']
        assert rule.dxf.fill.fgColor.rgb.endswith(color)
    assert ws.freeze_panes=='C2' and len(ws.tables)==1


def test_rerun_and_dynamic_column(inputs):
    for name in NAMES:
        p=inputs/(name+'.csv')
        with p.open(newline='') as f:r=csv.DictReader(f);h=r.fieldnames;rows=list(r)
        for row in rows:row['priority_category']=' '+row['priority_category'].lower()+' '
        h=['priority_category']+[c for c in h if c!='priority_category']
        with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=h);w.writeheader();w.writerows(rows)
    paths=generate_excel_exports(inputs);generate_excel_exports(inputs)
    for p in paths:
        w=load_workbook(p)['District Data'];k=list(w.conditional_formatting)[0]
        assert '$A2' in w.conditional_formatting[k][0].formula[0]


def test_missing_source_preserves_exports(inputs):
    paths=generate_excel_exports(inputs);before=paths[0].read_bytes()
    (inputs/(NAMES[1]+'.csv')).unlink()
    with pytest.raises(FileNotFoundError):generate_excel_exports(inputs)
    assert paths[0].read_bytes()==before
