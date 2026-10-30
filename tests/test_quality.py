from datetime import datetime,timezone,timedelta
import pytest
from src.data_quality import result,enforce,markdown_report


def test_quality_contract():
    check=result('invalid_population',False,0,1,['346'])
    assert set(check)=={'check_id','expected_result','actual_result','status','severity','affected_records','recommended_resolution'}
    assert check['status']=='FAIL'
    with pytest.raises(ValueError):enforce([check])

def test_warning_does_not_block():
    check=result('pension_estimation',False,'observed','estimated',severity='WARNING')
    assert check['status']=='WARN'
    enforce([check]);assert 'pension_estimation' in markdown_report([check])

@pytest.mark.parametrize('value,expected',[
 ('2026-10-30T00:00:00+00:00',True),
 ('2026-10-27T00:00:00+00:00',False),
 ('2026-10-31T00:00:00+00:00',False),
 ('2026-10-30T00:00:00',False),
 (None,False),('not-a-date',False)])
def test_ingestion_freshness(value,expected):
    from src.data_quality import ingestion_freshness
    valid,_=ingestion_freshness(value,24,datetime(2026,10,30,12,tzinfo=timezone.utc))
    assert valid is expected
