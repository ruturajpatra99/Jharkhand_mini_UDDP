"""Synthetic defects only; original public inputs are never edited by tests."""
import csv
import pytest
from pyspark.sql import functions as F
from pyspark.testing.utils import assertDataFrameEqual
from src.transform import numeric,normalize_name,normalize_column,clean_source
from .conftest import ROOT

@pytest.mark.parametrize('text,expected',[('1,23,456',123456),('1,234',1234),('001',1),('12.0',12),('1,2',None),('',None),('-1',None),('NaN',None),('12.5',None),('1.0000000001',None),('9223372036854775808',None)])
def test_numeric_contract(spark,text,expected):
    result=spark.createDataFrame([(text,)],['value']).select(numeric(F.col('value')).alias('parsed')).first()[0]
    assert result==expected

def test_name_alias(spark,mapping):
    frame=spark.createDataFrame([(' East  Singhbhum ',),('Seraikela-Kharsawan',)],['name'])
    actual=frame.select(normalize_name(F.col('name'),mapping['aliases']).alias('name'))
    expected=spark.createDataFrame([('purbi singhbhum',),('saraikela kharsawan',)],['name'])
    assertDataFrameEqual(actual,expected)

def fixture_frame(spark,settings,source,changes=None,duplicate=None):
    path=ROOT/'data/input'/settings['sources'][source]['filename']
    rows=list(csv.DictReader(path.open(encoding='utf-8-sig')))
    state={'demographics':'State name','housing':'State Name','pensions':'States/UTs'}[source]
    row=next(r for r in rows if r[state].strip().lower()=='jharkhand')
    row.update(changes or {});data=[row]
    if duplicate is not None:data.append(dict(row,**duplicate))
    columns=[normalize_column(c) for c in row]+['source_row']
    return spark.createDataFrame([tuple(r.values())+(i+2,) for i,r in enumerate(data)],columns)

@pytest.mark.parametrize('source,changes,reason',[
 ('demographics',{'District code':''},'missing_or_invalid_district_code'),
 ('demographics',{'District name':''},'missing_district_name'),
 ('demographics',{'District name':'Godda'},'district_code_name_mismatch'),
 ('demographics',{'Population':'0'},'invalid_population_or_households'),
 ('demographics',{'Households':'99999999'},'invalid_population_or_households'),
 ('demographics',{'Population':'invalid'},'invalid_numeric_population'),
 ('housing',{'State Code':'21'},'state_code_name_mismatch'),
 ('housing',{'Total Number of households':'101'},'housing_percentage_semantics_changed'),
 ('housing',{'Alternative_Source_Open':'102'},'percentage_above_100'),
 ('pensions',{'Old Age Pension Scheme':'-2'},'invalid_numeric_old_age'),
 ('pensions',{'Category':'Observed'},'pension_estimate_category_changed')])
def test_rejected_defects(spark,settings,mapping,source,changes,reason):
    good,bad,counts=clean_source(fixture_frame(spark,settings,source,changes),source,settings,mapping)
    assert good.count()==0
    assert reason in bad.first()['reason']
    assert counts['raw_rows']==counts['out_of_scope']+counts['accepted_source_rows']+counts['rejected_rows']
    spark.catalog.clearCache()

def test_exact_duplicate_keeps_first(spark,settings,mapping):
    good,bad,counts=clean_source(fixture_frame(spark,settings,'pensions',duplicate={}),'pensions',settings,mapping)
    assert good.count()==1 and bad.first()['reason']=='exact_duplicate'
    assert counts['rejected_rows']==1
    spark.catalog.clearCache()

def test_conflicting_duplicates_reject_all(spark,settings,mapping):
    good,bad,_=clean_source(fixture_frame(spark,settings,'pensions',duplicate={'Old Age Pension Scheme':'1'}),'pensions',settings,mapping)
    assert good.count()==0 and bad.count()==2
    assert all('conflicting_duplicate' in r.reason for r in bad.collect())
    spark.catalog.clearCache()

def test_scope_and_missing_state(spark,settings,mapping):
    a=fixture_frame(spark,settings,'pensions',{'States/UTs':'Odisha'})
    b=fixture_frame(spark,settings,'pensions',{'States/UTs':''}).withColumn('source_row',F.lit(3).cast('long'))
    _,bad,counts=clean_source(a.unionByName(b),'pensions',settings,mapping)
    assert counts['out_of_scope']==1 and bad.first()['reason']=='missing_state'
    spark.catalog.clearCache()

def test_required_columns_fail(spark,settings,mapping):
    with pytest.raises(ValueError,match='missing required columns'):
        clean_source(fixture_frame(spark,settings,'pensions').drop('district_code'),'pensions',settings,mapping)
