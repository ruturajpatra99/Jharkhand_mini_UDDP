from pathlib import Path
import json
import os
os.environ.setdefault("PYARROW_IGNORE_TIMEZONE","1")
import pytest
from src.spark_session import create_spark

ROOT=Path(__file__).resolve().parents[1]
@pytest.fixture(scope='session')
def spark():
    session=create_spark();yield session;session.stop()
@pytest.fixture
def settings():return json.loads((ROOT/'config/settings.json').read_text())
@pytest.fixture
def mapping():return json.loads((ROOT/'config/district_mapping.json').read_text())
