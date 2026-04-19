# Telco Stage Seed Contract

This is the prepared telco FLUID contract for the repo.

## What It Assumes

- the telco seed tables are already loaded into `SNOWFLAKE_STAGE_SCHEMA`
- the source tables already have Horizon-visible comments from `task metadata:apply`
- you have loaded `runtime/generated/fluid.local.env`
- you want a real telco contract story without changing dbt in this phase

## What It Builds

It materializes a demo-friendly Snowflake table named `TELCO_SUBSCRIBER_SUPPORT_POSTURE` in `SNOWFLAKE_FLUID_SCHEMA`.

The output combines:

- service records
- subscription and product offering context
- 30-day usage summaries
- customer interaction counts
- open support ticket counts
- latest service lifecycle activity

## Happy Path

```bash
set -a
source runtime/generated/fluid.local.env
set +a

.venv.fluid-demo/bin/fluid validate fluid/contracts/telco_stage_seed/contract.fluid.yaml
.venv.fluid-demo/bin/fluid plan fluid/contracts/telco_stage_seed/contract.fluid.yaml --out fluid/generated/telco-stage-plan.json --html runtime/plan.html
.venv.fluid-demo/bin/fluid apply fluid/contracts/telco_stage_seed/contract.fluid.yaml --yes
.venv.fluid-demo/bin/fluid verify fluid/contracts/telco_stage_seed/contract.fluid.yaml --strict
```

## Before The Live Apply

Make sure the landing data is already present:

```bash
task up
task seed:reset:confirm
task seed:generate
task seed:load
task metadata:apply
```

That prep can happen ahead of time so the live demo stays focused on FLUID.
