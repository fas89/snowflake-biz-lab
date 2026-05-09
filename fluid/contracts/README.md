# FLUID Contracts

This repo currently carries five prepared Snowflake-facing contracts: one smoke test, three pre-* ingestion contracts that replace the legacy Bronze anchors, and one staged-seed contract.

## `snowflake_smoke`

Use this first when you want the smallest possible Snowflake success.

- one embedded SQL build
- one tiny output table
- best for credential and permission proof

See [snowflake_smoke/README.md](snowflake_smoke/README.md).

## Pre-* ingestion contracts (`telco_pre1_billing_dlt`, `telco_pre2_party_airbyte`, `telco_pre3_usage_meltano`)

These three contracts replace the former passive Bronze contracts (`telco_seed_billing`, `telco_seed_party`, `telco_seed_usage`). Each pre-* contract describes the same Snowflake-landing data product (same `id`, `exposes`, schemas) but is now driven by an explicit Postgres → Snowflake acquisition pipeline using a different ingestion engine. Generate the source data into the `telco_source` Postgres database with `task seed:postgres:load`, then run the per-engine forge script to land it in Snowflake.

- `telco_pre1_billing_dlt` — invoice and invoice-charge tables ingested via **dlt** → published as `bronze.telco.billing_v1`
- `telco_pre2_party_airbyte` — party, account, service, subscription, and product-offering tables ingested via **PyAirbyte** (`source-postgres` + `destination-snowflake`) → published as `bronze.telco.party_v1`
- `telco_pre3_usage_meltano` — usage event, customer interaction, and trouble ticket tables ingested via **Meltano** (`tap-postgres` → `target-snowflake`) → published as `bronze.telco.usage_v1`

Each contract still acts as an upstream lineage anchor for the A1/A2/B1/B2 silver demo variants. Publish all three together via `task publish:pre`, then run the FLUID 11-stage pipeline per contract via `task fluid:11-stage CONTRACT=...` or via Jenkins (default `FLUID_CONTRACTS` parameter).

## `telco_stage_seed`

Use this after the seeded telco landing tables already exist in Snowflake.

- built on the staged telco seed model in this repo
- creates a demo-friendly Snowflake table from staged service, usage, ticket, and interaction data
- best for the real telco story without touching dbt in this phase

See [telco_stage_seed/README.md](telco_stage_seed/README.md).
