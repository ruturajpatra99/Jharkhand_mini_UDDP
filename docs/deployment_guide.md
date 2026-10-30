# Local execution and deployment

## Compatibility and installation

Use PySpark 3.5.6, py4j 0.10.9.7, Python 3.12.x and JDK 17. The actual tested interpreter is Python 3.12.14 on Linux; Python 3.12.10 is a Windows installer baseline. SQLite is bundled with Python and must be >=3.37. A separate database service/JDBC JAR is unnecessary. pytest 8.3.5 plus pandas 2.2.3, NumPy 1.26.4 and PyArrow 17.0.0 provide the testing environment. The Spark transformations themselves use DataFrames/SQL, not pandas or Arrow UDFs.

Follow the explicit interpreter commands in README. Run `scripts/verify_environment.py` before the full pipeline. It prints Python, Java, Spark and SQLite versions and executes a 24-row Spark action. Windows execution remains to be verified on the user's machine.

If pip build isolation cannot obtain setuptools, install setuptools/wheel in the virtual environment and retry with `--no-build-isolation`. This was necessary in the restricted execution environment after the Spark source archive had downloaded. Use a fresh environment; do not modify system Python or inherit unrelated packages locally.

## Windows troubleshooting

- `JAVA_GATEWAY_EXITED`: verify `java -version`, `JAVA_HOME` root and PATH; use JDK 17 and avoid multiple incompatible Java installs.
- Python worker mismatch: set `PYSPARK_PYTHON` to the same `.venv\Scripts\python.exe` used by the driver.
- Local host/firewall binding: set `SPARK_LOCAL_IP=127.0.0.1`; permit local Java communication according to your device policy.
- Missing native Hadoop library can be a warning; distinguish it from a failed action. If native Windows file permissions cause a real Hadoop error, use WSL2 with JDK 17/Python 3.12 or obtain/build a trusted compatible native Hadoop distribution. Do not install arbitrary executable downloads.
- Missing `pyarrow` during pytest collection: install `requirements-dev.txt`, not only the runtime requirements.
- SQLite `STRICT` syntax error: your Python build includes SQLite older than 3.37; install a compatible Python build.
- Existing pipeline lock: verify the owning PID and logs. Remove a stale lock only after confirming no writer is active.
- A run folder exists without a successful DB audit: treat it as a candidate/failed output, not published analytics.

## Scheduling locally

The project uses a modular Python batch entry point. Windows Task Scheduler can invoke `.venv\Scripts\python.exe` with arguments `-m src.main --work-dir runtime`, setting 'Start in' to the repository root. Set JAVA_HOME/PYSPARK_PYTHON in a wrapper script or service environment. Use one scheduled instance at a time.

On Linux, use a dedicated service account, protected runtime path and environment file with no secrets in Git. Example cron entry, after replacing paths:

```cron
0 2 * * * cd /opt/jharkhand-mini-uddp && /opt/jharkhand-mini-uddp/.venv/bin/python -m src.main --work-dir /var/lib/uddp >> /var/log/uddp.log 2>&1
```

Cron follows the server timezone. Set the server/scheduler timezone explicitly when 02:00 India time is intended. Timestamps in audit records are UTC. `logical_date` is a scheduler label, not the source reference year.

## Failure recovery and publication

1. Inspect `etl_run_log` and the run-specific `execution.jsonl` / quality report.
2. For rejected input, fix the input or mapping in a controlled new snapshot. Never silently alter counts to pass controls.
3. For pre-commit failures, the prior business snapshot remains intact. The audit records the failed attempt and `alerts.jsonl` receives a local event.
4. For an interrupted process, a RUNNING row/lock can remain. Confirm process termination; inspect database integrity and the latest committed output; remove only that stale lock and rerun.
5. If the database committed but the latest pointer did not update, use the SUCCEEDED run's `output_path` from SQLite and its publication hashes. Do not mark committed data as failed or modify immutable outputs.
6. Back up SQLite using its backup API or an offline copy after writers finish. A file copied during a live transaction is not the documented backup workflow.

Retries target transient extraction I/O only. A file-not-found/schema/quality failure is not retried. SQLite waits up to 30 seconds for a lock; there is no hidden distributed transaction retry loop. Failure alerts are local JSON; an approved operator may connect the hook to a messaging system later.

## Backfill

`python -m src.main --backfill-start 2026-10-28 --backfill-end 2026-10-30 --work-dir runtime`

The ordered range is capped at 32 days. Current input files are reused per logical date. To replay genuine history, supply the correct dated snapshot and versioned configuration per run and add observation-period keys to the model.

## Airflow and production migration

A future DAG can wrap extract → Spark validation/transform → staging load → merge/validate → publish, passing an immutable input fingerprint and logical date. Fail a task before downstream publication; keep retries scoped to transient operations. Do not let multiple Spark partitions write SQLite. For scale, use Parquet/object-storage staging, PostgreSQL COPY or a warehouse bulk loader and a controlled merge into partitioned facts. Introduce department/source contracts, credential management, SLA monitoring and lineage first. No server/cloud deployment is required or claimed by this assessment.
