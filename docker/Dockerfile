FROM mcr.microsoft.com/playwright/python:v1.50.0-jammy AS base

WORKDIR /app

# System deps only (NO Python install)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.prod.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.prod.txt

RUN python -m playwright install-deps chromium \
    && python -m playwright install chromium

COPY . .

FROM base AS api

ENV APP_PORT=8000
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS airflow

RUN pip install --no-cache-dir \
    "apache-airflow==2.9.0" \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.0/constraints-3.8.txt"

ENV AIRFLOW_HOME=/opt/airflow
RUN mkdir -p /opt/airflow/dags /opt/airflow/logs /opt/airflow/plugins

EXPOSE 8080