"""Run after installation: python scripts/verify_environment.py."""
import sys,sqlite3,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.spark_session import create_spark
import pyspark
print('Python:',sys.version)
print('SQLite:',sqlite3.sqlite_version)
print('PySpark:',pyspark.__version__)
subprocess.run(['java','-version'],check=True)
assert sqlite3.sqlite_version_info >= (3,37,0), 'SQLite STRICT requires 3.37+'
spark=create_spark()
try:
    assert spark.range(24).count()==24
    print('Spark action: PASS; 24 rows')
finally:spark.stop()
