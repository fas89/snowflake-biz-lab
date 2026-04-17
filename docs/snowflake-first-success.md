# Snowflake First Success

This is the quickest technical proof before the full GitLab-based demo.

## Recommended Order

1. start the local platform
2. seed Snowflake staging and apply metadata
3. prove the tiny smoke contract
4. move into the full Mac demo

## Step 1: Start The Local Platform

```bash
task up
task jenkins:up
task catalogs:up
task ps
```

## Step 2: Load Staging Data And Metadata

```bash
task seed:generate
task seed:load
task seed:verify
task metadata:apply
task metadata:verify
```

This gives you a real Snowflake landing zone before FLUID starts building silver-layer contracts on top of it.

## Step 3: Load Runtime Secrets Only When Needed

Create the ignored local runtime env file described in [Credentials](credentials.md), then load it:

```bash
set -a
source runtime/generated/fluid.local.env
set +a
```

## Step 4: Prove The Tiny Snowflake Contract

Use the released demo runtime or the local `.venv.fluid-demo` if you already bootstrapped it:

```bash
.venv.fluid-demo/bin/fluid validate fluid/contracts/snowflake_smoke/contract.fluid.yaml
.venv.fluid-demo/bin/fluid plan fluid/contracts/snowflake_smoke/contract.fluid.yaml --out fluid/generated/snowflake-smoke-plan.json --html
.venv.fluid-demo/bin/fluid apply fluid/contracts/snowflake_smoke/contract.fluid.yaml --yes
.venv.fluid-demo/bin/fluid verify fluid/contracts/snowflake_smoke/contract.fluid.yaml --strict
```

What this gives you:

- a tiny Snowflake-managed proof point
- a short validate/plan/apply/verify story
- a fast way to prove credentials, permissions, and warehouse settings

## Step 5: Move To The Full Demo

When you want the real local-Mac story with GitLab workspaces, Airflow generation, Jenkins generation, and standards export, jump to [Mac Demo Launchpad](mac-launchpad.md).
