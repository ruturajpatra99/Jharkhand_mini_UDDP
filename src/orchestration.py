"""Refactored batch runner: Spark transforms; one transactional SQLite writer."""
from __future__ import annotations
import hashlib,json,logging,os,sqlite3,time,uuid,shutil
from pathlib import Path
from typing import Callable,TypeVar
from . import data_quality as dq
from .extract import digest,extract,utcnow
from .load import connect,execute_script,export_rows,insert,bounded_rows,load_snapshot
from .transform import transform
from .scoring import score,sensitivity
from .features import build_features
from .spark_session import create_spark
from .excel_dashboard import generate_dashboard
from .excel_exports import generate_excel_exports
T=TypeVar('T');LOGGER=logging.getLogger('uddp')


def event(task: str, **fields: object) -> None:
    LOGGER.info(json.dumps(dict(timestamp=utcnow(),task=task,**fields),sort_keys=True))


def retry(function: Callable[[],T],attempts: int,delay: float) -> T:
    if attempts<1:raise ValueError('attempts must be >=1')
    for attempt in range(1,attempts+1):
        try:return function()
        except OSError as exc:
            if isinstance(exc,FileNotFoundError) or attempt==attempts:raise
            event('retry',attempt=attempt,error=str(exc));time.sleep(min(delay*2**(attempt-1),5))
    raise RuntimeError('unreachable')


def alert(work: Path,run_id: str,error: str) -> None:
    path=Path(os.environ.get('UDDP_ALERT_FILE',work/'outputs/alerts.jsonl'))
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a',encoding='utf-8') as file:file.write(json.dumps(dict(run_id=run_id,timestamp=utcnow(),error=error))+'\n')


def write_quality(folder: Path,checks: list) -> None:
    export_rows(folder/'data_quality_report.csv',checks)
    (folder/'data_quality_report.json').write_text(json.dumps(checks,indent=2))
    (folder/'data_quality_report.md').write_text(dq.markdown_report(checks))


def run(project: Path,work: Path,input_dir: Path,logical_date: str,settings_path: Path|None=None,
        fail_at: str|None=None,spark=None) -> dict:
    work.mkdir(parents=True,exist_ok=True)
    lock=work/'.pipeline.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    os.write(fd,str(os.getpid()).encode());os.close(fd)
    run_id=uuid.uuid4().hex;folder=work/'outputs/runs'/run_id;folder.mkdir(parents=True)
    handler=logging.FileHandler(folder/'execution.jsonl',encoding='utf-8');handler.setFormatter(logging.Formatter('%(message)s'))
    LOGGER.addHandler(handler);LOGGER.setLevel(logging.INFO)
    db=None;checks=[];started=False;owned_spark=spark is None
    try:
        settings=json.loads((settings_path or project/'config/settings.json').read_text())
        mapping=json.loads((project/'config/district_mapping.json').read_text())
        if set(settings['expected_codes'])!=set(mapping['canonical']):raise ValueError('Configured district codes differ from mapping')
        db=connect(work/'uddp.sqlite');execute_script(db,project/'sql/schema.sql')
        code_paths=sorted(list((project/'src').glob('*.py'))+list((project/'sql').glob('*.sql')))
        code_hash=hashlib.sha256(b''.join(p.name.encode()+p.read_bytes() for p in code_paths)).hexdigest()
        config_hash=hashlib.sha256(json.dumps(settings,sort_keys=True).encode()+json.dumps(mapping,sort_keys=True).encode()).hexdigest()
        db.execute("INSERT INTO etl_run_log(run_id,logical_date,started_at,status,config_sha256,code_sha256) VALUES (?,?,?,'RUNNING',?,?)",(run_id,logical_date,utcnow(),config_hash,code_hash));db.commit();started=True
        event('extract',run_id=run_id)
        _,manifests=retry(lambda:extract(input_dir,work/'data/bronze',settings,run_id),settings['retries'],settings['retry_delay_seconds'])
        insert(db,'source_ingestion_manifest',manifests)
        fingerprint=hashlib.sha256(''.join(m['sha256'] for m in manifests).encode()).hexdigest()
        db.execute('UPDATE etl_run_log SET input_fingerprint=? WHERE run_id=?',(fingerprint,run_id));db.commit()
        spark=spark or create_spark(settings['spark_master'])
        event('spark_transform',run_id=run_id,spark_version=spark.version)
        tables,bad,reconciliation,matches,unmatched=transform(spark,manifests,settings,mapping)
        rejected=bounded_rows(bad,settings['max_collect_rows']);match_rows=bounded_rows(matches);unmatched_rows=bounded_rows(unmatched)
        export_rows(folder/'rejected_records.csv',rejected,['source_name','source_row','reason','raw_record'])
        export_rows(folder/'row_reconciliation.csv',reconciliation)
        export_rows(folder/'district_match_report.csv',sorted(match_rows,key=lambda r:(r['district_code'],r['source_name'])))
        export_rows(folder/'unmatched_records.csv',unmatched_rows,['district_code','source_name','issue'])
        insert(db,'rejected_records',[dict(run_id=run_id,**r) for r in rejected]);db.commit()
        checks=dq.preflight(tables,rejected,reconciliation,match_rows,unmatched_rows,manifests,settings);dq.enforce(checks)
        for name,frame in tables.items():frame.createOrReplaceTempView(name)
        base=spark.sql((project/'sql/transformations.sql').read_text()).cache()
        mart=score(base,settings['weights'],settings['score_version']).cache()
        features=build_features(spark,mart,project/'sql').cache()
        checks+=dq.gold_checks(mart,features,settings);dq.enforce(checks)
        event('gold_validated',run_id=run_id)
        rows={name:sorted(bounded_rows(frame,settings['max_collect_rows']),key=lambda r:tuple(str(r.get(c,'')) for c in ['district_code','state_code','source_name','scheme'])) for name,frame in tables.items()}
        rows['mart_district_pension_outreach']=bounded_rows(mart.orderBy('district_code'))
        rows['ml_district_features']=bounded_rows(features.orderBy('district_code'))
        sensitivity_rows=bounded_rows(sensitivity(mart,settings['weights']).orderBy('scenario','district_code'))
        db.execute('BEGIN IMMEDIATE')
        load_snapshot(db,rows,settings['sqlite_batch_size'],fail_at=='after_load')
        checks+=dq.database_checks(db,settings);dq.enforce(checks)
        for name,values in rows.items():
            path=folder/f'{name}.csv' if name in ['mart_district_pension_outreach','ml_district_features'] else folder/'silver'/f'{name}.csv'
            export_rows(path,values)
        export_rows(folder/'score_sensitivity.csv',sensitivity_rows)
        dashboard=folder/'dashboard/Jharkhand_UDDP_Interactive_Dashboard.xlsx'
        generate_dashboard(folder,dashboard,run_id)
        excel_exports=generate_excel_exports(folder)
        checks.append(dq.result('pipeline_completion',True,'All stages succeeded','Spark validated and SQLite transaction ready'))
        write_quality(folder,checks)
        (folder/'settings.json').write_text(json.dumps(settings,indent=2));(folder/'district_mapping.json').write_text(json.dumps(mapping,indent=2))
        hashes={str(p.relative_to(folder)):digest(p) for p in sorted(folder.rglob('*.csv'))}
        publication=dict(run_id=run_id,logical_date=logical_date,output_path=str(folder.relative_to(work)),input_fingerprint=fingerprint,
                         config_sha256=config_hash,code_sha256=code_hash,csv_sha256=hashes,status='SUCCEEDED',
                         dashboard_path=str(dashboard.relative_to(work)),dashboard_sha256=digest(dashboard),
                         excel_exports={str(p.relative_to(work)):digest(p) for p in excel_exports})
        (folder/'publication.json').write_text(json.dumps(publication,indent=2))
        insert(db,'data_quality_results',[dict(run_id=run_id,**c) for c in checks])
        db.execute("UPDATE etl_run_log SET ended_at=?,status='SUCCEEDED',output_path=? WHERE run_id=?",(utcnow(),str(folder.relative_to(work)),run_id));db.commit()
        if fail_at=='after_commit':raise RuntimeError('Injected pointer failure after commit')
        # Keep immutable per-run workbook; publish a convenient latest copy atomically.
        latest_dashboard=work/'outputs/dashboard'/dashboard.name
        latest_dashboard.parent.mkdir(parents=True,exist_ok=True)
        dashboard_temp=latest_dashboard.with_suffix('.tmp')
        shutil.copyfile(dashboard,dashboard_temp);os.replace(dashboard_temp,latest_dashboard)
        for export in excel_exports:
            latest=work/'outputs'/export.name
            candidate=latest.with_suffix('.tmp')
            shutil.copyfile(export,candidate);os.replace(candidate,latest)
        temp=work/'outputs/latest_success.tmp';temp.write_text(json.dumps(publication,indent=2));os.replace(temp,work/'outputs/latest_success.json')
        event('succeeded',run_id=run_id,districts=len(rows['mart_district_pension_outreach']))
        return publication
    except Exception as exc:
        if db:db.rollback()
        if db and started and db.execute('SELECT status FROM etl_run_log WHERE run_id=?',(run_id,)).fetchone()[0]=='SUCCEEDED':
            alert(work,run_id,'Committed snapshot; dashboard/pointer publication issue: '+str(exc));raise
        # A publication error can occur after the tentative PASS was appended.
        # Replace it so the failure audit retains one row per run/check key.
        checks=[check for check in checks if check['check_id']!='pipeline_completion']
        checks.append(dq.result('pipeline_completion',False,'Successful complete run',str(exc),resolution='Inspect rejected rows and execution log; fix cause and rerun.'))
        write_quality(folder,checks)
        if db and started:
            insert(db,'data_quality_results',[dict(run_id=run_id,**c) for c in checks])
            db.execute("UPDATE etl_run_log SET ended_at=?,status='FAILED',error=? WHERE run_id=?",(utcnow(),str(exc),run_id));db.commit()
        alert(work,run_id,str(exc));event('failed',run_id=run_id,error=str(exc));raise
    finally:
        if spark:
            try:
                spark.catalog.clearCache()
                if owned_spark:spark.stop()
            except Exception as cleanup_error:
                event('spark_cleanup_failed',error=str(cleanup_error))
        if db:db.close()
        LOGGER.removeHandler(handler);handler.close();lock.unlink(missing_ok=True)
