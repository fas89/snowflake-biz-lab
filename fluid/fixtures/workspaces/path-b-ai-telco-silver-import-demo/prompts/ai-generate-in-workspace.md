# Spoken Prompt — B2 AI Forge (Generate Assets In Workspace)

> **Operator:** read this aloud while the forge interview runs. In demo mode the golden contract is replayed, so this file is only for the narrative.

Build a **silver aggregated subscriber360 data product** on Snowflake for the telco domain. Use the three bronze data products (`bronze.telco.billing_v1`, `bronze.telco.party_v1`, `bronze.telco.usage_v1`) as upstream lineage anchors.

The product should expose two marts:

- `mart_subscriber360_core`
- `mart_subscriber_health_scorecard`

Unlike B1, this variant must **generate** the dbt project and the Airflow DAG inside the workspace (no external references). After the contract is forged, `fluid generate transformation --engine dbt -o generated/dbt` and `fluid generate schedule --scheduler airflow -o generated/airflow` should produce the assets, and `fluid apply` should execute the generated build.

Resulting asset ID should be `silver.telco.subscriber360_generated_v1`.
