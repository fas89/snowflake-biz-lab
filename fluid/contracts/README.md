# FLUID Contracts

This repo currently carries three prepared Snowflake-facing contracts.

## `snowflake_smoke`

Use this first when you want the smallest possible Snowflake success.

- one embedded SQL build
- one tiny output table
- best for credential and permission proof

See [snowflake_smoke/README.md](snowflake_smoke/README.md).

## `telco_seed_sources`

Use this as the canonical bronze source contract for the seeded telco landing tables.

- points at the existing source tables in `SNOWFLAKE_STAGE_SCHEMA`
- acts as the upstream lineage anchor for the silver demo variants
- best for validate, plan, and marketplace lineage registration around the seeded sources

See [telco_seed_sources/README.md](telco_seed_sources/README.md).

## `telco_stage_seed`

Use this after the seeded telco landing tables already exist in Snowflake.

- built on the staged telco seed model in this repo
- creates a demo-friendly Snowflake table from staged service, usage, ticket, and interaction data
- best for the real telco story without touching dbt in this phase

See [telco_stage_seed/README.md](telco_stage_seed/README.md).
