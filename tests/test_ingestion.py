import csv,json
import pytest
from src.extract import extract,read_csv,digest
from src.orchestration import retry
from .conftest import ROOT

def test_bronze_unchanged(tmp_path,settings):
    _,manifest=extract(ROOT/'data/input',tmp_path/'bronze',settings,'fixture-run')
    for m in manifest:assert digest(ROOT/'data/input'/m['filename'])==digest(__import__('pathlib').Path(m['bronze_path']))==m['sha256']
    assert [m['raw_rows'] for m in manifest]==[640,640,24]

def test_missing_file(tmp_path,settings):
    with pytest.raises(FileNotFoundError):extract(tmp_path,tmp_path/'bronze',settings,'fixture-run')

def test_bad_csv(tmp_path):
    p=tmp_path/'bad.csv';p.write_text('a,a\n1,2\n')
    with pytest.raises(ValueError):read_csv(p)

def test_transient_retry():
    calls=[]
    def transient():
        calls.append(1)
        if len(calls)<3:raise OSError('temporary storage issue')
        return 7
    assert retry(transient,3,0)==7 and len(calls)==3

def test_invalid_data_not_retried():
    calls=[]
    def invalid():calls.append(1);raise ValueError('schema')
    with pytest.raises(ValueError):retry(invalid,3,0)
    assert len(calls)==1
