# Spoken Prompt — B2 AI Forge (Generate Assets In Workspace)

> **Operator:** read this aloud while the MCP-backed B2 forge runs. The scripted
> path passes equivalent context by reading Snowflake metadata from the seeded
> schema through forge-cli MCP.

Build a **silver aggregated subscriber360 data product** on Snowflake for the telco domain. Use the three bronze data products (`bronze.telco.billing_v1`, `bronze.telco.party_v1`, `bronze.telco.usage_v1`) as upstream lineage anchors.

The product should expose two marts:

- `mart_subscriber360_core`
- `mart_subscriber_health_scorecard`

Unlike B1, this variant must **generate** the dbt project and the Airflow DAG inside the workspace (no external references). The B2 flow starts from MCP-discovered Snowflake seeded tables, then generates dbt under `generated/dbt`, Airflow under `generated/airflow`, Jenkins CI, and finally applies the generated dbt build.

Resulting asset ID should be `silver.telco.subscriber360_generated_v1`.
