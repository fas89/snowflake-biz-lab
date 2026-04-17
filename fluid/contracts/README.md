# FLUID Contracts

This repo currently carries two prepared Snowflake-facing contracts.

## `snowflake_smoke`

Use this first when you want the smallest possible Snowflake success.

- one embedded SQL build
- one tiny output table
- best for credential and permission proof

See [snowflake_smoke/README.md](snowflake_smoke/README.md).

## `telco_stage_seed`

Use this after the seeded telco landing tables already exist in Snowflake.

- built on the staged telco seed model in this repo
- creates a demo-friendly Snowflake table from staged service, usage, ticket, and interaction data
- best for the real telco story without touching dbt in this phase

See [telco_stage_seed/README.md](telco_stage_seed/README.md).
