FROM apache/airflow:2.9.1

USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl git && \
    rm -rf /var/lib/apt/lists/*

USER airflow
RUN pip install --no-cache-dir \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.1/constraints-3.12.txt" \
    "apache-airflow-providers-snowflake==5.4.0" \
    "psycopg2-binary" \
    "pyyaml>=6.0"
