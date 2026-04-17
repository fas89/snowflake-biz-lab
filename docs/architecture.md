# Architecture Notes

- Snowflake is the only warehouse target in this repo.
- `seed/` owns raw file generation and landing-table loads.
- `dbt/` owns cleaned staging views or tables in `SNOWFLAKE_DBT_SCHEMA`.
- `governance/` owns comments, tags, contacts, classification hooks, and DMF hooks.
- `airflow/` is intentionally scaffold-only in this phase. The stack is present, but no DAG code is checked in yet.
- `jenkins/` provides CI bootstrap and Snowflake-gated validation without orchestrating Airflow.
