import pytest
from src.scoring import score,validate_weights,INPUTS

def test_weights(settings):
    validate_weights(settings['weights'])
    with pytest.raises(ValueError):validate_weights({'x':1})

def test_constant_features_and_ties(spark,settings):
    columns=['district_code']+[v[0] for v in INPUTS.values()]
    base=spark.createDataFrame([(str(346+i),1.,1.,.5,20.,4.) for i in reversed(range(24))],columns)
    rows=score(base,settings['weights'],'test').orderBy('priority_rank').collect()
    assert [r.district_code for r in rows]==[str(346+i) for i in range(24)]
    assert all(r.pension_outreach_priority_score==0 for r in rows)
    assert [r.priority_category for r in rows]==['High']*8+['Medium']*8+['Low']*8

def test_missing_score_input_fails(spark,settings):
    from pyspark.sql import functions as F
    columns=['district_code']+[v[0] for v in INPUTS.values()]
    base=spark.createDataFrame([('346',1.,1.,.5,20.,4.)],columns).withColumn('crude_literacy_share',F.lit(None).cast('double'))
    with pytest.raises(ValueError,match='Missing scoring input'):score(base,settings['weights'],'test')
