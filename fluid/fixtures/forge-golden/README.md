# Forge Golden Fixtures

This folder holds **deterministic replay copies** of contracts that `fluid forge` produced during a controlled, off-stage run. The launchpad's demo-mode blocks copy one of these golden files over `contract.fluid.yaml` instead of calling the live LLM, so the on-stage flow is reproducible byte-for-byte.

## Why this exists

`fluid forge` delegates to an upstream LLM that this repo cannot currently seed or pin. On a live demo, the same spoken prompt can produce different build IDs, different column names, or a subtly different contract shape. Any shape change can break the downstream `validate → plan → apply → generate ci` chain.

The golden fixture removes that risk without giving up the AI story: you still narrate what `fluid forge` would do and still end up with an AI-authored contract — it just happens to be the one you recorded and reviewed ahead of time.

This is also called out in the [FLUID Gap Register](../../../docs/fluid-gap-register.md) under "AI `forge` for Snowflake + dbt silver aggregation". Once forge-cli exposes a seed or deterministic-replay flag upstream, the launchpad can switch back to a live call and this folder can shrink to an evergreen fallback.

## Structure

```
fluid/fixtures/forge-golden/
  B1-ai-reference-external/
    contract.fluid.yaml   # drop-in for B1 (referenced dbt + referenced Airflow)
  B2-ai-generate-in-workspace/
    contract.fluid.yaml   # drop-in for B2 (generated dbt + generated Airflow)
```

Each subdirectory contains exactly what the launchpad copies to `contract.fluid.yaml`. If B2's demo-mode flow also needs pre-generated `dbt/` and `airflow/` assets, check those in alongside the contract file so the single `cp` step mirrors the full forge output.

## How to refresh a golden

Run this once, off-stage, against the real forge LLM. Then inspect the output before committing.

```bash
cd "$EXISTING_DBT_WORKSPACE/variants/B1-ai-reference-external"
set -a && source "$FLUID_SECRETS_FILE" && set +a
"$FLUID_DEV_BIN" init subscriber360-external --provider snowflake --yes
cd subscriber360-external
"$FLUID_DEV_BIN" forge --provider snowflake --domain telco --target-dir .
"$FLUID_DEV_BIN" validate contract.fluid.yaml
"$FLUID_DEV_BIN" plan contract.fluid.yaml --out runtime/plan.json --html

# review runtime/plan.html; if you are happy with what forge produced, copy it in:
cp contract.fluid.yaml "$LAB_REPO/fluid/fixtures/forge-golden/B1-ai-reference-external/contract.fluid.yaml"
```

Repeat for `B2-ai-generate-in-workspace`, pointing at `fluid/fixtures/forge-golden/B2-ai-generate-in-workspace/contract.fluid.yaml`.

Commit the result to the repo so every demo starts from the same byte-identical contract.

## Verification after refresh

Against a freshly copied golden contract:

1. `fluid validate` and `fluid plan` succeed with no warnings
2. `scripts/get_first_build_id.py <contract>` prints the expected build id
3. `fluid apply --build <id>` completes cleanly against a reset Snowflake demo schema
4. `fluid generate ci` produces a Jenkinsfile the B1/B2 pipelines can pick up

## When to skip demo mode

If you are working on forge-cli itself (for example, iterating on prompt templates or provider support) you want the live LLM call, not the replay. The launchpad B1/B2 sections keep both forms side by side — the demo-mode block for presentations and the live `fluid forge` command for contributors — with clear labels.
