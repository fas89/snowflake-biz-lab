# Snowflake Smoke Contract

This is the smallest FLUID contract in the repo.

## Why It Exists

Use this when you want to prove:

- the CLI is installed correctly
- Snowflake credentials are wired correctly
- `validate`, `plan`, `apply`, and `verify` all work end to end

## What It Creates

- schema: `SNOWFLAKE_FLUID_SCHEMA`
- table: `TELCO_SMOKE_TABLE`

## Happy Path

```bash
set -a
source runtime/generated/fluid.local.env
set +a

.venv.fluid-demo/bin/fluid validate fluid/contracts/snowflake_smoke/contract.fluid.yaml
.venv.fluid-demo/bin/fluid plan fluid/contracts/snowflake_smoke/contract.fluid.yaml --out fluid/generated/snowflake-smoke-plan.json
.venv.fluid-demo/bin/fluid apply fluid/contracts/snowflake_smoke/contract.fluid.yaml --yes
.venv.fluid-demo/bin/fluid verify fluid/contracts/snowflake_smoke/contract.fluid.yaml --strict
```

Once this contract feels comfortable, move to [the telco contract](../telco_stage_seed/README.md).
