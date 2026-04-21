# Spoken Prompt — B1 AI Forge (External References)

> **Operator:** read this aloud while the forge interview runs. In demo mode the golden contract is replayed, so this file is only for the narrative.

Build a **silver aggregated subscriber360 data product** on Snowflake for the telco domain. Use the three bronze data products (`bronze.telco.billing_v1`, `bronze.telco.party_v1`, `bronze.telco.usage_v1`) as upstream lineage anchors.

The product should expose two marts:

- `mart_subscriber360_core` — the unified subscriber view joining account, service, and subscription hubs
- `mart_subscriber_health_scorecard` — a quality/health scorecard per subscriber derived from usage, trouble-ticket, and interaction signals

Model the product as a Data Vault 2.0 silver layer backed by the existing `dbt_dv2_subscriber360` project and Airflow DAG at `airflow_subscriber360/dags/telco_subscriber360_pipeline.py`. **Reference** those assets externally rather than generating new dbt or Airflow code inside the workspace.

Resulting asset ID should be `silver.telco.subscriber360_external_ref_v1`.
