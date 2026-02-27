# airflow/dags/dag_friendlies.py

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_ROOT = "/home/callmegallas/accel_football_api/gogainde-data"
PYTHON = f"{PROJECT_ROOT}/.venv/bin/python"

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
    "execution_timeout": timedelta(hours=1),
}

with DAG(
    dag_id="ingest_friendlies_senegal",
    description="Ingestion matchs amicaux du Sénégal",
    schedule="0 5 * * 1",
    start_date=datetime(2026, 2, 25),
    catchup=False,
    default_args=default_args,
    tags=["football", "friendlies"],
    max_active_runs=3,
) as dag:

    BashOperator(
        task_id="run_friendlies",
        bash_command="cd /app && python -m pipeline.ingest_friendlies",
    #     bash_command="""
    # cd "/home/callmegallas/accel_football_api/gogainde-data" && \
    # /home/callmegallas/accel_football_api/gogainde-data/.venv/bin/python -m pipeline.ingest_friendlies
    # """
    )