# FLUID Contracts

This repo currently carries five prepared Snowflake-facing contracts: one smoke test, three bronze source contracts split by subject area, and one staged-seed contract.

## `snowflake_smoke`

Use this first when you want the smallest possible Snowflake success.

- one embedded SQL build
- one tiny output table
- best for credential and permission proof

See [snowflake_smoke/README.md](snowflake_smoke/README.md).

## Bronze source contracts (`telco_seed_billing`, `telco_seed_party`, `telco_seed_usage`)

These three contracts are the canonical bronze source anchors for the seeded telco landing tables. They split the former single `telco_seed_sources` contract into one contract per subject area, which lines up with the TM Forum SID domains and makes each bronze product independently ownable in the marketplace.

- `telco_seed_billing` — invoice and invoice-charge sources → published as `bronze.telco.billing_v1`
- `telco_seed_party` — party, account, service, subscription, and product-offering sources → published as `bronze.telco.party_v1`
- `telco_seed_usage` — usage event, customer interaction, and trouble ticket sources → published as `bronze.telco.usage_v1`

Each contract points at the existing source tables in `SNOWFLAKE_STAGE_SCHEMA` and acts as an upstream lineage anchor for the silver demo variants. Publish all three together during the Bronze Anchor scenario — see the bronze section in [Dev Source Launchpad (Mac)](../../docs/dev-source-launchpad-mac.md) or [Dev Source Launchpad (Windows)](../../docs/dev-source-launchpad-windows.md).

## `telco_stage_seed`

Use this after the seeded telco landing tables already exist in Snowflake.

- built on the staged telco seed model in this repo
- creates a demo-friendly Snowflake table from staged service, usage, ticket, and interaction data
- best for the real telco story without touching dbt in this phase

See [telco_stage_seed/README.md](telco_stage_seed/README.md).
