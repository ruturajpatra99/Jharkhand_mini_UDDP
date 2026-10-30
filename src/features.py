"""Execute the versioned feature contract in Spark SQL."""
from pathlib import Path
from pyspark.sql import DataFrame, SparkSession


def build_features(spark: SparkSession, mart: DataFrame, sql_dir: Path) -> DataFrame:
    mart.createOrReplaceTempView('mart_district_pension_outreach')
    return spark.sql((sql_dir/'features.sql').read_text())
