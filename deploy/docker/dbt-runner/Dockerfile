FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl git && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    "dbt-core==1.8.2" \
    "dbt-snowflake==1.8.2" \
    "pyyaml>=6.0" \
    "snowflake-connector-python==3.10.0"

RUN groupadd --gid 1000 lab && \
    useradd --uid 1000 --gid 1000 --create-home --shell /usr/sbin/nologin lab

WORKDIR /opt/project
USER lab
CMD ["sleep", "infinity"]
