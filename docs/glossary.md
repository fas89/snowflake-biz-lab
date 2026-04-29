# Glossary

One page of definitions for the terms the launchpads and playbooks use.
If you are new to this repo, keep this tab open while reading
[Getting Started](getting-started.md).

## Core concepts

- **FLUID** — the data-product authoring and operations layer exposed by the
  `fluid` CLI. Every command (`fluid validate`, `fluid plan`, `fluid apply`,
  `fluid publish`, `fluid generate ci`, …) is part of the FLUID surface.
- **contract (`contract.fluid.yaml`)** — the source-of-truth YAML that
  declares a data product: its name, owner, exposes (output ports),
  consumes (input ports), schema, policies, builds, and schedule. Everything
  downstream is derived from it.
- **expose** — an output port of a data product: a named table/view/API that
  the product publishes. Each expose gets its own ODCS contract in DMM.
- **consume** — a declared dependency on another product's expose. `fluid
  publish --target datamesh-manager` turns product-to-product consumes into
  Entropy `Access` agreements, which are the DMM graph edges. These product
  consumes are not mirrored as DMM SourceSystems or ODPS input ports.
- **forge-cli** — the source repository that builds `data-product-forge`
  (the pip package that ships `fluid`). Lives at
  `https://github.com/agentics-transformation/forge-cli`.

## Data-product specifications

- **ODCS** — Open Data Contract Standard (v3.1.0). The schema-level contract
  shape that DMM stores per expose at
  `/api/datacontracts/{productId}.{exposeId}`.
- **OPDS** — the Linux-Foundation "Open Data Product Standard" emitter
  (`fluid generate standard --format opds`). Legacy shape with
  `{id, reference}` on input ports.
- **ODPS-Bitol** — the newer "ODPS v1.0.0" data-product shape from Bitol
  (`fluid generate standard --format odps-bitol`). `additionalProperties:
  false`; input/output ports carry `name` + `contractId` rather than `id` +
  `reference`. DMM uses this shape when `provider_hint=odps`.
- **DPS** — the original "Data Product Specification" shape (pre-ODPS).
  Entropy Data treats DPS as legacy; this lab defaults to ODPS-Bitol.

## Publishing & catalogs

- **DMM / Data Mesh Manager** — Entropy Data's catalog product. The local
  lab runs a Community Edition at `http://localhost:8095`. `fluid publish
  --target datamesh-manager` pushes the contract here.
- **Horizon** — a separate catalog target (not the default for this lab).
- **umbrella contract** — an ODCS contract `fluid publish` writes at
  `/api/datacontracts/{productId}` (no expose suffix) as a defensive resolution
  stub. The per-expose contracts at
  `/api/datacontracts/{productId}.{exposeId}` are what the schema actually
  lives in.
- **provider hint** — passed to DMM to select the data-product
  specification shape (`dps` vs `odps`). The lab defaults to `odps`.

## Pipeline lifecycle (11 stages)

`fluid generate ci --system jenkins` emits a pipeline that walks these
stages. Each `RUN_STAGE_N_*` toggle on the Jenkins job can skip one.

1. **bundle** — deterministic `.tgz` of the contract + MANIFEST.json
   (SHA-256 merkle root). Root of trust for every downstream stage.
2. **validate** — schema + SQL (sqlglot) + OpenAPI validators.
3. **generate artifacts** — ODCS + ODPS-Bitol + schedule + policies fanout.
4. **validate artifacts** — re-verify MANIFEST SHA-256 + per-format schemas.
5. **diff** — compare contract against live warehouse schema (drift gate).
6. **plan** — compute DDL operations; emits `bundleDigest` + `planDigest`.
7. **apply** — execute DDL. Modes: `dry-run`, `amend`, `create-only`,
   `amend-and-build`, `replace`, `replace-and-build`. The
   `amend-and-build` mode combines schema evolution with a dbt rebuild in
   one step (what the variant playbooks use).
8. **policy apply** — IAM / GRANT enforcement.
9. **verify** — post-apply reconciliation against the live warehouse
   (strict mode fails on any mismatch, including nullable↔required).
10. **publish** — push catalog artifacts (DMM / Horizon / …).
11. **schedule sync** — push generated DAGs to the scheduler (Airflow /
    MWAA / Composer / Astronomer / Prefect / Dagster).

## Scenarios in this lab

- **Bronze** — three seed-backed bronze products (`telco_seed_billing`,
  `telco_seed_party`, `telco_seed_usage`) that feed every silver variant.
- **Path A (ready-made)** — two silver variants derived from curated dbt
  assets:
  - **A1 external-reference** — references a dbt project sitting in
    `reference-assets/`.
  - **A2 internal-reference** — the same idea but the dbt project lives
    inside the workspace.
- **Path B (AI-forge)** — AI-authored silver variants:
  - **B1 ai-reference-external** — live-forged with Gemini or OpenAI from the
    seeded telco context, then hardened with stable lab guardrails so the
    external dbt/Jenkins/Airflow flow can run consistently.
  - **B2 ai-generate-in-workspace** — MCP-forged from the seeded Snowflake
    schema, then generated directly in the workspace.

## Install tracks

- **demo-release** — installs the latest `data-product-forge` release
  from TestPyPI, resolved dynamically at bootstrap time. Use this when
  showing the demo in front of people.
- **dev-source** — installs `forge-cli` in editable mode from a local
  checkout (`pip install -e ../forge-cli`) so you can change FLUID
  behaviour and retest immediately. Use this when fixing forge-cli.

## Workspaces

- **Workspace A (`path-a-telco-silver-product-demo`)** — the synthetic
  GitLab demo repo under `gitlab/`, hosts A1 + A2 variants + their
  `Jenkinsfile` checked out by the Jenkins SCM pipelines.
- **Workspace B (`path-b-ai-telco-silver-import-demo`)** — the AI/MCP forge
  equivalent for B1 / B2. Both variants are wired to the lab's Jenkins instance.

Both workspaces live under `./gitlab/` (gitignored) and are bootstrapped
from templates at `fluid/fixtures/workspaces/` via
`task workspaces:bootstrap`.
