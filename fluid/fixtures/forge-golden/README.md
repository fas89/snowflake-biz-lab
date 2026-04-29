# Forge Golden Fixtures

This folder holds markers for scenarios that used to rely on deterministic replay copies. B1 and B2 intentionally have no replay contracts here; B1 calls `task b1:forge:ai`, and B2 calls `task b2:forge:mcp`.

## Why this exists

`fluid forge` delegates to an upstream LLM that this repo cannot fully seed or pin. On a live demo, the same spoken prompt can produce different build IDs, different column names, or a subtly different contract shape. Any shape change can break the downstream `validate -> plan -> apply -> generate ci` chain.

The active B1 and B2 paths solve that differently: they preserve raw provider/MCP output and then apply lab guardrails for runnable Snowflake/dbt flows.

This is also called out in the [FLUID Gap Register](../../../docs/fluid-gap-register.md) under "AI `forge` for Snowflake + dbt silver aggregation". Once forge-cli can emit the exact B1 operational envelope directly, this folder can shrink to an evergreen fallback.

## Structure

```
fluid/fixtures/forge-golden/
  B1-ai-reference-external/
    README.md             # marker: B1 intentionally has no replay contract
  B2-ai-generate-in-workspace/
    README.md             # marker: B2 intentionally has no replay contract
```

Do not add B1 or B2 golden contracts. The active playbooks intentionally run
their provider-backed generation steps.

## Active B1 Path

For the active B1 flow, use `task b1:forge:ai`; for B2, use `task b2:forge:mcp`.
