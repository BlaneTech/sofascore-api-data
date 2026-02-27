from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_ROOT = "/home/callmegallas/accel_football_api/gogainde-data"
PYTHON = f"{PROJECT_ROOT}/.venv/bin/python"

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    "execution_timeout": timedelta(hours=4),
}

with DAG(
    dag_id="live_tracker",
    description="Lance le live tracker pendant les jours de match",
    schedule="0 13 * * *",
    start_date=datetime(2026, 2, 25),
    catchup=False,
    default_args=default_args,
    tags=["football", "live"],
    max_active_runs=3,

) as dag:

    BashOperator(
        task_id="run_live_tracker",
        bash_command="cd /app && python -m app.live_tracker",
    #   bash_command="""
    # cd "/home/callmegallas/accel_football_api/gogainde-data" && \
    # /home/callmegallas/accel_football_api/gogainde-data/.venv/bin/python -m app.live_tracker
    # """
    )