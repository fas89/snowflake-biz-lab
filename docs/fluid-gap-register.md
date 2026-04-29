# FLUID Gap Register

This register tracks only source-verified `forge-cli` gaps that still affect the
Snowflake biz lab. It was rechecked against the local `forge-cli` working branch
on 2026-04-26.

Stale notes were removed during this audit. In the current source, native dbt
build dispatch exists, dbt adapter execution has local/container escape hatches,
`llm_models.json` is included as package data, MCP source-catalog tools exist,
and the lab's existing dbt/Airflow/publish paths are working demo composition
rather than standalone `forge-cli` defects.

## Confirmed Current Gaps

### `apply --mode *-and-build` needs first-class build resolution

- Current observed behavior:
  The current source has a native `fluid_build.build_runners` dispatcher for
  dbt and Python builds. This is no longer the old "dbt falls into a Python
  script executor" issue. The remaining gap is the apply surface: build modes
  still rely on an explicit build ID for the build branch, and the apply/build
  semantics are not yet a clean "DDL apply, then selected build" flow.
- Why it matters in the demo:
  Operators should be able to run the generated contract without copying a raw
  `builds[].id` into every command or Jenkins parameter when the contract has a
  single obvious build.
- Likely `forge-cli` area:
  `fluid_build/cli/apply.py`, `fluid_build/forge/core/apply_modes.py`, and
  `fluid_build/build_runners/*`.
- Acceptance criteria:
  `fluid apply contract.fluid.yaml --mode amend-and-build` can resolve the
  single-build case automatically, present a clear selector/error for multiple
  builds, preserve the data-loss gate for destructive modes, and run the build
  after the provider apply step.

### `apply -> Jenkins` needs a first-class deployment handoff

- Current observed behavior:
  `fluid generate ci --system jenkins` writes a Jenkinsfile, but `fluid apply`
  does not expose a Jenkins trigger or first-class handoff. The lab therefore
  creates Pipeline-from-SCM jobs with helper scripts.
- Why it matters in the demo:
  The story lands more cleanly if generated CI becomes an intentional deployment
  handoff instead of a separate lab orchestration step.
- Likely `forge-cli` area:
  `fluid_build/cli/generate_ci.py`, `fluid_build/cli/scaffold_ci.py`,
  `fluid_build/cli/apply.py`, and post-apply reporting hooks.
- Acceptance criteria:
  After generating Jenkins CI, `fluid apply` can either trigger the generated
  Jenkins path directly or emit a structured Jenkins handoff payload with the
  workspace, contract, plan, build ID, and suggested parameters.

### MCP `forge_from_source` needs product-grade physical intent controls

- Current observed behavior:
  MCP source tools work and can read the seeded Snowflake metadata through
  `credentials.credential_id`. The `forge_from_source` tool writes a contract
  plus logical sidecar from catalog metadata, but it does not yet produce the
  complete B2-style product envelope by itself: stable lab product IDs, Bronze
  input ports, Snowflake table bindings, schedule/CI intent, and runnable
  subscriber-360 dbt marts still come from lab hardening.
- Why it matters in the demo:
  B2 should feel like "MCP reads Snowflake, forges the product, then the normal
  flow runs" while keeping deterministic output for every user.
- Likely `forge-cli` area:
  `fluid_build/cli/mcp.py`, `fluid_build/forge_datamodel/from_catalog/*`,
  `fluid_build/forge_datamodel/emit/*`, and transformation generation.
- Acceptance criteria:
  A source-backed MCP call can accept enough business/domain intent to produce a
  deterministic Snowflake silver product contract and generated dbt project that
  are directly runnable without lab-specific rewrite passes.

### Generated artifact timestamps are not byte-stable

- Current observed behavior:
  Several generated artifacts still use wall-clock timestamps in headers or
  provenance, for example scheduler codegen paths that call `datetime.utcnow()`.
  The business content is stable, but repeated generation can create noisy diffs.
- Why it matters in the demo:
  B1/B2 intentionally preserve raw AI/MCP receipts while keeping final demo
  outputs deterministic. Wall-clock headers make it harder to see meaningful
  changes.
- Likely `forge-cli` area:
  Scheduler/codegen helpers and staged data-model artifact writers.
- Acceptance criteria:
  A deterministic mode, or `SOURCE_DATE_EPOCH`-style environment variable,
  fixes generated timestamps so identical inputs produce byte-identical outputs.

## Fixed During This Audit

- `fluid init NAME --provider snowflake --yes </dev/null` no longer reaches the
  interactive creation-mode prompt in the current local source.
- `fluid forge --context prompt.md` can now load Markdown/text prompt files as
  freeform context, and context validation errors no longer crash through the
  `CLIError` constructor.
