# FLUID Contracts

This repo currently carries five prepared Snowflake-facing contracts: one smoke test, three pre-* ingestion contracts that replace the legacy Bronze anchors, and one staged-seed contract.

## `snowflake_smoke`

Use this first when you want the smallest possible Snowflake success.

- one embedded SQL build
- one tiny output table
- best for credential and permission proof

See [snowflake_smoke/README.md](snowflake_smoke/README.md).

## Pre-* ingestion contracts (`telco_pre1_billing_dlt`, `telco_pre2_party_airbyte`, `telco_pre3_usage_meltano`)

These three contracts replace the former passive Bronze contracts (`telco_seed_billing`, `telco_seed_party`, `telco_seed_usage`). Each pre-* contract uses **FLUID 0.7.3's `builds[].pattern: acquisition` block** with a different ingestion engine. `fluid apply` (stage 7) natively invokes the matching forge-cli runner under `forge-cli/fluid_build/build_runners/<engine>/` — there are no per-engine shim scripts to maintain. The contract's `schemaEvolution.policy: strict` prevents the engine from mutating the FLUID-applied DDL. Same `id`, `exposes`, and Snowflake bindings as the legacy contracts, so every silver variant downstream consumes them unchanged.

| Contract | Engine | Source tables (Postgres `telco_source.telco.*`) | Published as |
| --- | --- | --- | --- |
| `telco_pre1_billing_dlt` | `dlt` | `invoice`, `invoice_charge` | `bronze.telco.billing_v1` |
| `telco_pre2_party_airbyte` | `airbyte` (embedded deployment) | `party`, `account`, `service`, `subscription`, `product_offering` | `bronze.telco.party_v1` |
| `telco_pre3_usage_meltano` | `meltano` (`tap-postgres` → `target-snowflake`) | `usage_event`, `customer_interaction`, `trouble_ticket` | `bronze.telco.usage_v1` |

Pre-condition: the source Postgres tables must be populated first — run `task seed:postgres:load` to load the generator's CSVs into `telco_source.telco.*`. Then run the lifecycle per scenario:

- `task pre1:demo` / `pre2:demo` / `pre3:demo` — chains `seed:postgres:load` + `fluid:11-stage CONTRACT=...` for one scenario
- `task pre:all:demo` — runs all three sequentially so the bronze landing schema is fully populated for downstream silver scenarios
- `task publish:pre` — publishes only the `fluid publish` step for all three contracts (used when you only need DMM registration after data is already loaded)
- `task jenkins:sync SCENARIO={pre1|pre2|pre3}` — registers the per-pre Jenkins job pointing at the co-located Jenkinsfile (`fluid/contracts/telco_pre*_*/Jenkinsfile`)

## `telco_stage_seed`

Use this after the seeded telco landing tables already exist in Snowflake.

- built on the staged telco seed model in this repo
- creates a demo-friendly Snowflake table from staged service, usage, ticket, and interaction data
- best for the real telco story without touching dbt in this phase

See [telco_stage_seed/README.md](telco_stage_seed/README.md).
