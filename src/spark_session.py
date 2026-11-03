"""Local Spark lifecycle; the driver is the only SQLite writer."""
from __future__ import annotations
import os
import sys
from pyspark.sql import SparkSession


def create_spark(master: str = 'local[2]') -> SparkSession:
    os.environ.setdefault('SPARK_LOCAL_IP', '127.0.0.1')
    os.environ.setdefault('PYSPARK_PYTHON', sys.executable)
    spark = (SparkSession.builder.master(master).appName('Jharkhand-Mini-UDDP')
             .config('spark.sql.shuffle.partitions', '2')
             .config('spark.default.parallelism', '2')
             .config('spark.ui.enabled', 'false')
             # Repeated local runs must not retain unbounded plan/debug metadata.
             .config('spark.sql.maxPlanStringLength', '8192')
             .config('spark.sql.ui.retainedExecutions', '10')
             .config('spark.ui.retainedJobs', '10')
             .config('spark.ui.retainedStages', '20')
             .config('spark.sql.session.timeZone', 'UTC')
             .config('spark.sql.ansi.enabled', 'false')
             .getOrCreate())
    spark.sparkContext.setLogLevel('ERROR')
    return spark
