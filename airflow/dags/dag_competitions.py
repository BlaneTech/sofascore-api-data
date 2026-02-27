from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_ROOT = "/home/callmegallas/accel_football_api/gogainde-data"
PYTHON = f"{PROJECT_ROOT}/.venv/bin/python"

default_args = {
    "owner": "airflow",
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
    "execution_timeout": timedelta(hours=3),
}

with DAG(
    dag_id="ingest_competitions",
    description="Ingestion compétitions officielles",
    schedule="0 4 * * *",
    start_date=datetime(2026, 2, 25),
    catchup=False,
    default_args=default_args,
    tags=["football", "competitions"],
    max_active_runs=3,
) as dag:

    BashOperator(
        task_id="run_competitions",
        bash_command="cd /app && python -m pipeline.ingest_afcon"    #     bash_command="""
    # cd "/home/callmegallas/accel_football_api/gogainde-data" && \
    # /home/callmegallas/accel_football_api/gogainde-data/.venv/bin/python -m pipeline.ingest_afcon
    # """
    )