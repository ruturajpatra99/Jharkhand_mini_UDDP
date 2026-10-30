"""Explainable Spark expressions; pension rates are estimates, not eligibility coverage."""
from __future__ import annotations
from functools import reduce
from pyspark.sql import DataFrame, Window, functions as F

INPUTS={'dilapidated':('dilapidated_pct',False),
        'open_defecation':('open_defecation_pct',False),
        'low_literacy':('crude_literacy_share',True),
        'low_old_age_rate':('estimated_old_age_per_1000_population',True),
        'low_widow_rate':('estimated_widow_per_1000_population',True)}


def validate_weights(weights: dict) -> None:
    if set(weights)!=set(INPUTS) or any(v<0 for v in weights.values()) or abs(sum(weights.values())-1)>1e-9:
        raise ValueError('Weights must cover five inputs, be nonnegative and sum to one')


def normalize(frame: DataFrame) -> DataFrame:
    window=Window.rowsBetween(Window.unboundedPreceding,Window.unboundedFollowing)
    for name,(column,invert) in INPUTS.items():
        value=F.col(column).cast('double')
        low,high=F.min(value).over(window),F.max(value).over(window)
        scaled=(high-value)/(high-low) if invert else (value-low)/(high-low)
        frame=frame.withColumn('normalized_'+name,F.when(high==low,F.lit(0.0)).otherwise(scaled))
    return frame


def rank_scores(frame: DataFrame) -> DataFrame:
    all_rows=Window.rowsBetween(Window.unboundedPreceding,Window.unboundedFollowing)
    frame=frame.withColumn('priority_rank',F.row_number().over(Window.orderBy(F.desc('pension_outreach_priority_score'),F.asc('district_code'))))
    n=F.count('*').over(all_rows)
    tail=F.floor(n*.33+.5)
    return frame.withColumn('priority_category',F.when(F.col('priority_rank')<=tail,'High').when(F.col('priority_rank')>n-tail,'Low').otherwise('Medium'))


def score(base: DataFrame, weights: dict, version: str) -> DataFrame:
    validate_weights(weights)
    required=[v[0] for v in INPUTS.values()]
    if base.filter(reduce(lambda a,b:a|b,[F.col(c).isNull()|F.isnan(c) for c in required])).limit(1).count():
        raise ValueError('Missing scoring input: no silent imputation or weight redistribution')
    frame=normalize(base)
    expression=sum(F.col('normalized_'+name)*weight for name,weight in weights.items())*100
    return rank_scores(frame.withColumn('pension_outreach_priority_score',F.round(expression,8)).withColumn('score_version',F.lit(version)))


def sensitivity(scored: DataFrame, weights: dict) -> DataFrame:
    """Ten +/-0.1 scenarios and a no-pension scenario; reuse normalized inputs."""
    cases=[]
    for name in weights:
        for delta in [-.1,.1]:
            altered=dict(weights);altered[name]=max(0,altered[name]+delta)
            total=sum(altered.values());altered={k:v/total for k,v in altered.items()}
            cases.append((name+('_minus_0.1' if delta<0 else '_plus_0.1'),altered))
    no_pension={k:(0 if 'rate' in k else v/.8) for k,v in weights.items()}
    cases.append(('exclude_estimated_pension_rates',no_pension))
    results=[]
    for scenario,weight in cases:
        value=F.round(100*sum(F.col('normalized_'+k)*v for k,v in weight.items()),8)
        changed=rank_scores(scored.select('district_code',F.col('priority_rank').alias('baseline_rank'),value.alias('pension_outreach_priority_score')))
        results.append(changed.select(F.lit(scenario).alias('scenario'),'district_code','baseline_rank',F.col('priority_rank').alias('scenario_rank'),(F.col('priority_rank')-F.col('baseline_rank')).alias('rank_change'),'pension_outreach_priority_score','priority_category'))
    return reduce(DataFrame.unionByName,results)
