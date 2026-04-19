# Telco Seed Sources Contract

This is the canonical bronze source contract for the seeded telco Snowflake tables.

Use it as the upstream lineage anchor for the silver Subscriber 360 demo variants.

## What It Represents

- existing Snowflake source tables in `SNOWFLAKE_STAGE_SCHEMA`
- source-level expose definitions for the tables used by the silver demos
- the upstream contract that silver products consume and publish lineage against

## Happy Path

```bash
set -a
source runtime/generated/fluid.local.env
set +a

.venv.fluid-demo/bin/fluid validate fluid/contracts/telco_seed_sources/contract.fluid.yaml
.venv.fluid-demo/bin/fluid plan fluid/contracts/telco_seed_sources/contract.fluid.yaml --out fluid/generated/telco-seed-sources-plan.json --html
```

Use this contract for validate, plan, and publish. The actual source-table creation is still handled by:

```bash
task seed:reset:confirm
task seed:generate
task seed:load
task metadata:apply
task metadata:verify
```
