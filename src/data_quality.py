"""Structured checks with expected/actual values, severity and recovery guidance."""
from __future__ import annotations
from datetime import datetime, timezone
import json
from pyspark.sql import functions as F


def result(name: str, okay: bool, expected, actual, affected=None,
           resolution: str='Correct source or mapping, then rerun.', severity: str='ERROR') -> dict:
    return dict(check_id=name,expected_result=str(expected),actual_result=str(actual),
        status='PASS' if okay else ('WARN' if severity=='WARNING' else 'FAIL'),severity=severity,
        affected_records=json.dumps(affected or [],sort_keys=True),recommended_resolution=resolution if not okay else 'None')


def enforce(checks: list) -> None:
    if failed := [r['check_id'] for r in checks if r['status']=='FAIL']:
        raise ValueError('Data quality gate failed: '+', '.join(failed))


def ingestion_freshness(timestamp, max_age_hours: float, now: datetime | None = None) -> tuple[bool, float | None]:
    try:
        age=((now or datetime.now(timezone.utc))-datetime.fromisoformat(timestamp)).total_seconds()/3600
        return 0 <= age <= max_age_hours, age
    except (ValueError,TypeError):
        return False,None


def preflight(tables: dict, rejected: list, reconciliation: list, matches: list,
              unmatched: list, manifests: list, settings: dict) -> list:
    checks=[]
    for r in reconciliation:
        s=r['source_name']
        accounted=r['out_of_scope']+r['accepted_source_rows']+r['rejected_rows']
        checks.append(result(s+'_row_reconciliation',accounted==r['raw_rows'],r['raw_rows'],accounted))
        checks.append(result(s+'_expected_districts',r['accepted_source_rows']==24,24,r['accepted_source_rows']))
        bad=[x for x in rejected if x['source_name']==s and x['reason']!='exact_duplicate']
        checks.append(result(s+'_valid_records',not bad,0,len(bad),[{'record':x['source_row'],'reason':x['reason']} for x in bad]))
        dup=[x for x in rejected if x['source_name']==s and x['reason']=='exact_duplicate']
        checks.append(result(s+'_exact_duplicates',not dup,0,len(dup),[x['source_row'] for x in dup],severity='WARNING'))
    checks.append(result('district_matching',not unmatched,0,len(unmatched),unmatched))
    for name,frame in tables.items():
        keys=['district_code','scheme'] if name=='fact_pension_beneficiaries' else ['state_code','scheme'] if name=='pension_state_rollup' else ['source_name','district_code'] if name=='district_name_mapping' else ['district_code']
        duplicates=frame.groupBy(*keys).count().filter('count>1').count()
        checks.append(result(name+'_unique_key',duplicates==0,0,duplicates))
    dim=tables['dim_district']
    duplicate_names=dim.groupBy('district_name').count().filter('count>1').count()
    checks.append(result('district_names_unique',duplicate_names==0,0,duplicate_names))
    totals={r['scheme']:r['estimated_beneficiary_count'] for r in tables['pension_state_rollup'].collect()}
    for scheme,expected in settings['pension_totals'].items():
        checks.append(result('pension_total_'+scheme,totals.get(scheme)==expected,expected,totals.get(scheme),resolution='Investigate discrepancy; never rescale supplied estimates.'))
    now=datetime.now(timezone.utc)
    for m in manifests:
        fresh,age=ingestion_freshness(m.get('ingestion_timestamp'),settings['max_ingestion_age_hours'],now)
        checks.append(result(m['source_name']+'_ingestion_freshness',fresh,f"0..{settings['max_ingestion_age_hours']} hours",age))
    checks += [result('observation_currency',False,'Current aligned observation periods','Census 2011; pension period unknown',severity='WARNING',resolution='Obtain documented current reference periods before operational use.'),
               result('pension_estimation',False,'Observed district beneficiary counts','Supplied estimates preserved',severity='WARNING',resolution='Validate against official district observations when authorized.'),
               result('eligibility_denominators',False,'Verified elderly and widow eligible populations','Unavailable; corresponding fields NULL',severity='WARNING',resolution='Obtain eligible-population denominators before claiming scheme coverage.'),
               result('household_universe',False,'Verified comparable household universe','Demographic Households count; housing percentages separate',severity='WARNING',resolution='Reconcile official household definitions before interpreting cross-source totals.')]
    return checks


def gold_checks(mart,features,settings: dict) -> list:
    checks=[]
    for label,frame in [('gold',mart),('ml',features)]:
        n=frame.count();unique=frame.select('district_code').distinct().count()
        checks.append(result(label+'_cardinality',n==unique==24,'24 rows and 24 keys',f'{n} rows / {unique} keys'))
    invalid=mart.filter('pension_outreach_priority_score IS NULL OR pension_outreach_priority_score<0 OR pension_outreach_priority_score>100').count()
    checks.append(result('score_range',invalid==0,0,invalid))
    cats={r['priority_category']:r['count'] for r in mart.groupBy('priority_category').count().collect()}
    checks.append(result('priority_thirds',cats=={'High':8,'Medium':8,'Low':8},'8 / 8 / 8',cats))
    invalid=features.filter("high_priority != CASE WHEN priority_category='High' THEN 1 ELSE 0 END").count()
    checks.append(result('target_consistency',invalid==0,0,invalid))
    wrong=mart.filter(F.abs(F.col('estimated_old_age_per_1000_population')-1000*F.col('old_age_estimated_beneficiaries')/F.col('population'))>1e-9).count()
    checks.append(result('old_age_rate_calculation',wrong==0,0,wrong))
    wrong=features.join(mart.select('district_code','female_population','population'),'district_code').filter(F.abs(F.col('female_population_share')-F.col('female_population')/F.col('population'))>1e-9).count()
    checks.append(result('feature_share_calculation',wrong==0,0,wrong))
    missing=set(['district_code','pension_values_estimated','high_priority','score_version'])-set(features.columns)
    checks.append(result('required_feature_columns',not missing,'none missing',sorted(missing)))
    return checks


def database_checks(db,settings: dict) -> list:
    broken=[tuple(r) for r in db.execute('PRAGMA foreign_key_check')]
    return [result('sqlite_foreign_keys',not broken,0,len(broken),broken),
            result('sqlite_gold_count',db.execute('SELECT COUNT(*) FROM mart_district_pension_outreach').fetchone()[0]==24,24,db.execute('SELECT COUNT(*) FROM mart_district_pension_outreach').fetchone()[0])]


def markdown_report(checks: list) -> str:
    counts={s:sum(r['status']==s for r in checks) for s in ['PASS','WARN','FAIL']}
    text='# Data quality report\n\n'+str(counts)+'\n\n| Check | Expected | Actual | Status | Severity | Resolution |\n|---|---|---|---|---|---|\n'
    for r in checks:
        text+='| '+' | '.join(str(r[k]).replace('|','/').replace('\n',' ') for k in ['check_id','expected_result','actual_result','status','severity','recommended_resolution'])+' |\n'
    return text+'\nAffected record identifiers and rejection details are retained in the JSON/CSV reports.\n'
