# Architecture Notes

- Snowflake is the only warehouse target in this repo.
- `seed/` owns raw file generation and landing-table loads.
- `dbt/` owns cleaned staging views or tables in `SNOWFLAKE_DBT_SCHEMA`.
- `fluid/` now owns FLUID contracts, demo runbooks, track checks, and future contract-adjacent assets.
- `governance/` owns comments, tags, contacts, classification hooks, and DMF hooks.
- `runtime/generated/` is the local-only home for ignored FLUID/Snowflake credential files.
- `runtime/wheels/` is reserved for backup demo install artifacts.
- `airflow/` is intentionally scaffold-only in this phase. The stack is present, but no DAG code is checked in yet.
- `jenkins/` provides CI bootstrap and Snowflake-gated validation without orchestrating Airflow.
- Hosted GitLab is the intended contract system of record later, but no `.gitlab-ci.yml` or FLUID CI generation is added in this phase.
