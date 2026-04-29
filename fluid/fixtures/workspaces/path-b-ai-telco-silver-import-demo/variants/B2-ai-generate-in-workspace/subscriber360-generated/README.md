# B2 MCP Product Directory

This directory is intentionally light in the tracked workspace template.

Run `task b2:forge:mcp` from the lab repo to read the seeded Snowflake schema
through forge-cli MCP and create the B2 contract, dbt project, Airflow DAG, and
Jenkinsfile here.

The raw MCP contract/model receipt is kept under `runtime/generated/mcp-forge/`
during a run; runtime output stays untracked in the workspace repo.
