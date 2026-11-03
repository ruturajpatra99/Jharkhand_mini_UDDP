import csv,json,sqlite3
from pathlib import Path
import pytest
from src.orchestration import run
from src.load import connect,load_snapshot,upsert,bounded_rows
from .conftest import ROOT

@pytest.fixture(scope='module')
def completed(tmp_path_factory,spark):
    work=tmp_path_factory.mktemp('pipeline')
    first=run(ROOT,work,ROOT/'data/input','2026-10-30',spark=spark)
    second=run(ROOT,work,ROOT/'data/input','2026-10-30',spark=spark)
    return work,first,second

def test_end_to_end_and_idempotency(completed):
    work,first,second=completed
    assert len(second['excel_exports'])==2
    for path,digest in second['excel_exports'].items():
        import hashlib
        assert hashlib.sha256((work/path).read_bytes()).hexdigest()==digest
        assert (work/'outputs'/Path(path).name).read_bytes()==(work/path).read_bytes()
    for name in ['mart_district_pension_outreach.csv','ml_district_features.csv','score_sensitivity.csv']:
        assert first['csv_sha256'][name]==second['csv_sha256'][name]
    db=connect(work/'uddp.sqlite')
    assert db.execute('SELECT COUNT(*) FROM mart_district_pension_outreach').fetchone()[0]==24
    assert db.execute('SELECT COUNT(*) FROM fact_pension_beneficiaries').fetchone()[0]==72
    assert db.execute("SELECT COUNT(*) FROM etl_run_log WHERE status='SUCCEEDED'").fetchone()[0]==2
    assert list(db.execute('PRAGMA foreign_key_check'))==[]
    db.close()

def test_source_estimates_preserved(completed,settings):
    work,_,second=completed;db=connect(work/'uddp.sqlite')
    raw=list(csv.DictReader((ROOT/'data/input'/settings['sources']['pensions']['filename']).open(encoding='utf-8-sig')))
    columns={'old_age':'Old Age Pension Scheme','widow':'Widow Pension Scheme','disability':'Divyangjan /Disability Pension Scheme'}
    for row in raw:
        for scheme,column in columns.items():assert db.execute('SELECT estimated_beneficiary_count FROM fact_pension_beneficiaries WHERE district_code=? AND scheme=?',(row['District Code'],scheme)).fetchone()[0]==int(row[column])
    db.close()

def test_actual_formula_independent(completed,settings):
    work,_,_=completed;db=connect(work/'uddp.sqlite');rows=[dict(r) for r in db.execute('SELECT * FROM mart_district_pension_outreach')]
    inputs={'dilapidated':('dilapidated_pct',False),'open_defecation':('open_defecation_pct',False),'low_literacy':('crude_literacy_share',True),'low_old_age_rate':('estimated_old_age_per_1000_population',True),'low_widow_rate':('estimated_widow_per_1000_population',True)}
    for r in rows:
        expected=0
        for name,(col,invert) in inputs.items():
            lo=min(x[col] for x in rows);hi=max(x[col] for x in rows)
            norm=0 if hi==lo else (hi-r[col] if invert else r[col]-lo)/(hi-lo)
            expected+=norm*settings['weights'][name]*100
        assert r['pension_outreach_priority_score']==pytest.approx(expected,abs=1e-7)
        assert r['estimated_widow_per_1000_population']==pytest.approx(1000*r['widow_estimated_beneficiaries']/r['population'],abs=1e-9)
        assert r['elderly_share'] is None and r['old_age_eligible_coverage'] is None
    db.close()

def test_transaction_rollback(completed):
    work,_,_=completed;db=connect(work/'uddp.sqlite')
    before=[tuple(r) for r in db.execute('SELECT * FROM mart_district_pension_outreach ORDER BY district_code')]
    db.execute('BEGIN IMMEDIATE')
    with pytest.raises(RuntimeError):load_snapshot(db,{},fail=True)
    db.rollback()
    assert before==[tuple(r) for r in db.execute('SELECT * FROM mart_district_pension_outreach ORDER BY district_code')]
    db.close()

def test_upsert_changes_existing_row(completed):
    work,_,_=completed;db=connect(work/'uddp.sqlite')
    row=dict(db.execute('SELECT * FROM fact_pension_beneficiaries LIMIT 1').fetchone());before=row['estimated_beneficiary_count'];row['estimated_beneficiary_count']+=1
    db.execute('BEGIN IMMEDIATE');upsert(db,'fact_pension_beneficiaries',[row])
    assert db.execute('SELECT COUNT(*) FROM fact_pension_beneficiaries').fetchone()[0]==72
    assert db.execute('SELECT estimated_beneficiary_count FROM fact_pension_beneficiaries WHERE district_code=? AND scheme=?',(row['district_code'],row['scheme'])).fetchone()[0]==before+1
    db.rollback();db.close()

def test_database_fk_and_negative_constraints(completed):
    work,_,_=completed;db=connect(work/'uddp.sqlite')
    with pytest.raises(sqlite3.IntegrityError):db.execute("INSERT INTO fact_pension_beneficiaries VALUES('999','old_age',1,NULL,1)")
    db.rollback()
    with pytest.raises(sqlite3.IntegrityError):db.execute("UPDATE fact_pension_beneficiaries SET estimated_beneficiary_count=-1")
    db.rollback();db.close()

def test_lock_is_not_removed(tmp_path):
    lock=tmp_path/'.pipeline.lock';lock.write_text('existing')
    with pytest.raises(FileExistsError):run(ROOT,tmp_path,ROOT/'data/input','2026-10-30')
    assert lock.read_text()=='existing'

def test_failed_run_is_recorded(tmp_path):
    with pytest.raises(FileNotFoundError):run(ROOT,tmp_path,tmp_path/'missing','2026-10-30')
    db=connect(tmp_path/'uddp.sqlite')
    assert db.execute('SELECT status FROM etl_run_log').fetchone()[0]=='FAILED'
    assert not (tmp_path/'outputs/latest_success.json').exists()
    assert (tmp_path/'outputs/alerts.jsonl').exists()
    db.close()

def test_bounded_collection(spark):
    with pytest.raises(ValueError,match='collection limit'):bounded_rows(spark.range(3),2)


def test_orchestrated_failure_preserves_published_snapshot(completed,spark):
    work,_,_=completed
    pointer=(work/'outputs/latest_success.json').read_bytes()
    db=connect(work/'uddp.sqlite');before=[tuple(r) for r in db.execute('SELECT * FROM mart_district_pension_outreach ORDER BY district_code')];db.close()
    with pytest.raises(RuntimeError,match='Injected test failure'):
        run(ROOT,work,ROOT/'data/input','2026-10-30',fail_at='after_load',spark=spark)
    db=connect(work/'uddp.sqlite')
    assert before==[tuple(r) for r in db.execute('SELECT * FROM mart_district_pension_outreach ORDER BY district_code')]
    assert db.execute("SELECT COUNT(*) FROM etl_run_log WHERE status='FAILED'").fetchone()[0]>=1
    assert (work/'outputs/latest_success.json').read_bytes()==pointer
    assert not (work/'.pipeline.lock').exists()
    db.close()


def test_committed_snapshot_survives_pointer_failure(completed,spark):
    work,_,_=completed
    pointer=(work/'outputs/latest_success.json').read_bytes()
    with pytest.raises(RuntimeError,match='pointer failure'):
        run(ROOT,work,ROOT/'data/input','2026-10-30',fail_at='after_commit',spark=spark)
    db=connect(work/'uddp.sqlite')
    row=db.execute('SELECT * FROM etl_run_log ORDER BY started_at DESC LIMIT 1').fetchone()
    assert row['status']=='SUCCEEDED'
    assert (work/row['output_path']/'publication.json').exists()
    assert (work/'outputs/latest_success.json').read_bytes()==pointer
    assert db.execute('SELECT COUNT(*) FROM mart_district_pension_outreach').fetchone()[0]==24
    db.close()


def test_publication_failure_records_one_completion_check(completed,spark,monkeypatch):
    import src.orchestration as orchestration
    work,_,_=completed
    pointer=(work/'outputs/latest_success.json').read_bytes()
    original=orchestration.write_quality
    def fail_once_on_pass(folder,checks):
        if any(c['check_id']=='pipeline_completion' and c['status']=='PASS' for c in checks):
            raise OSError('Injected quality publication failure')
        return original(folder,checks)
    monkeypatch.setattr(orchestration,'write_quality',fail_once_on_pass)
    with pytest.raises(OSError,match='quality publication failure'):
        run(ROOT,work,ROOT/'data/input','2026-10-30',spark=spark)
    db=connect(work/'uddp.sqlite')
    latest=db.execute('SELECT run_id,status FROM etl_run_log ORDER BY started_at DESC LIMIT 1').fetchone()
    assert latest['status']=='FAILED'
    rows=db.execute("SELECT status FROM data_quality_results WHERE run_id=? AND check_id='pipeline_completion'",(latest['run_id'],)).fetchall()
    assert len(rows)==1 and rows[0]['status']=='FAIL'
    assert (work/'outputs/latest_success.json').read_bytes()==pointer
    assert db.execute('SELECT COUNT(*) FROM mart_district_pension_outreach').fetchone()[0]==24
    assert not (work/'.pipeline.lock').exists()
    db.close()


def test_dashboard_integrated_and_failure_rollback(completed,spark,monkeypatch):
    import hashlib
    import src.orchestration as orchestration
    from openpyxl import load_workbook
    work,_,publication=completed
    path=work/publication['dashboard_path']
    assert load_workbook(path).sheetnames[0]=='Executive Dashboard'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==publication['dashboard_sha256']
    latest=work/'outputs/dashboard/Jharkhand_UDDP_Interactive_Dashboard.xlsx'
    assert latest.read_bytes()==path.read_bytes()
    pointer=(work/'outputs/latest_success.json').read_bytes();before=latest.read_bytes()
    def fail(*args,**kwargs):raise OSError('Injected dashboard failure')
    monkeypatch.setattr(orchestration,'generate_dashboard',fail)
    with pytest.raises(OSError,match='dashboard failure'):
        run(ROOT,work,ROOT/'data/input','2026-10-30',spark=spark)
    assert latest.read_bytes()==before and (work/'outputs/latest_success.json').read_bytes()==pointer
    db=connect(work/'uddp.sqlite')
    assert db.execute("SELECT status FROM etl_run_log ORDER BY started_at DESC LIMIT 1").fetchone()[0]=='FAILED'
    assert db.execute('SELECT COUNT(*) FROM mart_district_pension_outreach').fetchone()[0]==24
    db.close()
