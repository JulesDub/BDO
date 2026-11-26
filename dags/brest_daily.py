"""Airflow 3 DAG for optional local orchestration via Docker Compose."""
from __future__ import annotations

from datetime import datetime, timezone
import subprocess
import sys
from airflow.sdk import dag, task


@dag(
    dag_id="brest_open_data_refresh",
    schedule="0 7 * * *",
    start_date=datetime(2026, 11, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    tags=["brest", "open-data", "portfolio"],
)
def brest_open_data_refresh():
    @task(retries=1)
    def ingest_validate_publish():
        result = subprocess.run(
            [sys.executable, "-m", "src.pipeline", "--allow-stale-sites"],
            cwd="/opt/airflow/brest",
            capture_output=True,
            text=True,
            check=True,
        )
        print(result.stdout)
        return "Publication terminée"

    ingest_validate_publish()


brest_open_data_refresh()
