FROM apache/airflow:2.9.1

USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl git && \
    rm -rf /var/lib/apt/lists/*

USER airflow
RUN pip install --no-cache-dir \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.1/constraints-3.12.txt" \
    "apache-airflow-providers-snowflake==5.7.1" \
    "dbt-core==1.8.2" \
    "dbt-snowflake==1.8.2" \
    "psycopg2-binary" \
    "pyyaml>=6.0" \
    "snowflake-connector-python>=3.12,<4.0"
