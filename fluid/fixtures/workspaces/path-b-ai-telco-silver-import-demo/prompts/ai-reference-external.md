# Spoken Prompt — B1 AI Forge (External References)

> **Operator:** read this aloud while the live forge step runs. The scripted B1 path passes equivalent structured context to Gemini/OpenAI and stores the raw AI receipt under `runtime/generated/ai-forge/`.

Build a **silver aggregated subscriber360 data product** on Snowflake for the telco domain. Use the three bronze data products (`bronze.telco.billing_v1`, `bronze.telco.party_v1`, `bronze.telco.usage_v1`) as upstream lineage anchors.

The product should expose two marts:

- `mart_subscriber360_core` — the unified subscriber view joining account, service, and subscription hubs
- `mart_subscriber_health_scorecard` — a quality/health scorecard per subscriber derived from usage, trouble-ticket, and interaction signals

Model the product as a Data Vault 2.0 silver layer backed by the existing `dbt_dv2_subscriber360` project. **Reference** that dbt project externally for execution, while the B1 flow generates a transformation preview and a fresh Airflow schedule from the live AI contract.

Resulting asset ID should be `silver.telco.subscriber360_ai_external_v1`.
