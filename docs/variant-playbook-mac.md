# Variant Playbook (Mac)

Shared Bronze / A1 / A2 commands for both the demo-release and dev-source tracks on macOS. The track launchpad sets up the FLUID runtime and the `FLUID_CLI` variable; this playbook runs the variants.

AI-forge scenarios **B1** and **B2** are staged for a future release — see [Coming Soon](#coming-soon--ai-forge-variants-b1-b2).

## Before You Start

Your track launchpad must have already:

- bootstrapped a FLUID runtime (Workspace A venv for demo-release; a single lab-level venv for dev-source)
- exported `FLUID_CLI` — either `fluid` (demo-release, with the Workspace A venv active) or `"$FLUID_DEV_BIN"` (dev-source)
- loaded `$LAB_REPO`, `$GREENFIELD_WORKSPACE`, `$FLUID_SECRETS_FILE`

If a new shell loses the demo-release venv between runs, re-activate with `source "$GREENFIELD_WORKSPACE/.venv/bin/activate"` before A1 or A2. Dev-source uses a single `$FLUID_DEV_BIN` across all variants.

## Mandatory Plan Verification Gate

Every variant must stop after `fluid plan`. Use this gate inside each variant block:

```bash
"$FLUID_CLI" validate contract.fluid.yaml
"$FLUID_CLI" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
```

Then review [Plan Verification Checklist](plan-verification-checklist.md). Do not run `"$FLUID_CLI" apply --mode amend-and-build --build …` until the checklist is complete and the plan is confirmed.

> **What changed:** the old `--build <id>` shorthand auto-upgrades to `--mode amend-and-build --build <id>` with a deprecation warning. The 11-stage pipeline requires the explicit `--mode` flag (see [Apply Modes](#apply-modes-11-stage-pipeline) below). `--target` replaces `--catalog` for `fluid publish` — `--catalog` still works one more release with a deprecation warning.

## Apply Modes (11-Stage Pipeline)

`fluid apply --mode <mode>` is the stage-7 surface of the 11-stage pipeline:

| Mode | DDL | DML | Existing data |
|---|---|---|---|
| `dry-run` | render only | — | untouched |
| `create-only` | `CREATE IF NOT EXISTS` + fail-if-exists | — | untouched |
| `amend` (default) | `ALTER ADD COLUMN IF NOT EXISTS`; views `CREATE OR REPLACE` | — | preserved; new cols NULL |
| `amend-and-build` | same as `amend` | `dbt run` + `dbt test` | preserved; transforms refreshed |
| `replace` | auto-snapshot → `CREATE OR REPLACE TABLE` | — | **dropped**; backup retained |
| `replace-and-build` | same as `replace` | `dbt run --full-refresh` | **dropped**; rebuilt |

Destructive modes (`replace*`) require `--allow-data-loss` when `FLUID_ENV != dev` or the target has rows. Every variant below uses `--mode amend-and-build --build <id>` because each owns dbt assets that need to re-run after the schema evolves.

## Scenario Vocabulary

- **Bronze** — upstream lineage anchor, three contracts: `telco_seed_billing`, `telco_seed_party`, `telco_seed_usage`
- **A1** — external-reference silver contract
- **A2** — internal-reference silver contract

### Install-Mode Partition (Jenkins CI surface)

Each variant's generated `Jenkinsfile` is pinned to one install mode — chosen when you run `fluid generate ci`. This determines how the Jenkins container installs `fluid` at build time:

| Variant | `--install-mode` | Where Jenkins gets `fluid` | Demo track |
|---|---|---|---|
| **A1** | `dev-source` | Bind-mounted `/forge-cli-src` in the Jenkins container (see [dev-source-launchpad-mac.md](dev-source-launchpad-mac.md)) | lab iteration — contributors testing forge-cli changes against real A1 contract |
| **A2** | `dev-source` | Same bind mount as A1 | lab iteration |

Bronze contracts (`telco_seed_*`) don't publish Jenkinsfiles today; they're published to the catalog directly via `fluid publish` without a CI step.

Use [Scenario Validation Matrix](scenario-validation-matrix.md) for the exact contract paths, dbt roots, DAG paths, DAG IDs, Jenkinsfile paths, and expose names.

## Bronze Anchor Scenario

Bronze is published as **three contracts**, one per subject area: billing, party, and usage. They are the upstream lineage anchors for the silver variants.

Load Snowflake secrets once, then validate, plan, and publish each contract:

```bash
cd "$LAB_REPO"
set -a
source "$FLUID_SECRETS_FILE"
set +a

for domain in billing party usage; do
  contract="fluid/contracts/telco_seed_${domain}/contract.fluid.yaml"
  "$FLUID_CLI" validate "$contract"
  "$FLUID_CLI" plan "$contract" --out "fluid/contracts/telco_seed_${domain}/runtime/plan.json" --html
  "$FLUID_CLI" publish "$contract" --target datamesh-manager
done
```

Open the three plan reports to review them:

```bash
open fluid/contracts/telco_seed_billing/runtime/plan.html
open fluid/contracts/telco_seed_party/runtime/plan.html
open fluid/contracts/telco_seed_usage/runtime/plan.html
```

Validation:

- review each of the three bronze plans against [Plan Verification Checklist](plan-verification-checklist.md)
- open the DMM marketplace at [http://localhost:8095](http://localhost:8095) and confirm all three data products appear under the **telco** domain:
  - `bronze.telco.billing_v1`
  - `bronze.telco.party_v1`
  - `bronze.telco.usage_v1`
- no Airflow, dbt, or Jenkins assets are expected for this scenario

## Workspace A: Ready-Made Variants

Demo-release only — activate Workspace A's venv before running A1 or A2:

```bash
source "$GREENFIELD_WORKSPACE/.venv/bin/activate"
```

### A1 External Reference

```bash
cd "$GREENFIELD_WORKSPACE/variants/A1-external-reference"
set -a
source "$FLUID_SECRETS_FILE"
set +a
"$FLUID_CLI" validate contract.fluid.yaml
"$FLUID_CLI" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
"$FLUID_CLI" apply contract.fluid.yaml --mode amend-and-build --build dv2_subscriber360_reference_build --yes --report runtime/apply_report.html
# A1 is a dev-source scenario — Jenkinsfile installs fluid from the
# /forge-cli-src bind mount. See docs/dev-source-launchpad-mac.md.
"$FLUID_CLI" generate ci contract.fluid.yaml --system jenkins --install-mode dev-source --out Jenkinsfile
git add .
git commit -m "Refresh external-reference silver variant"
"$FLUID_CLI" publish contract.fluid.yaml --target datamesh-manager
```

Validation:

- open Airflow at [http://localhost:8085](http://localhost:8085) and confirm DAG `telco_subscriber360_reference`
- run `(cd "$LAB_REPO" && task dbt:docs:refresh SCENARIO=A1)` then open [http://localhost:8086](http://localhost:8086) and confirm `mart_subscriber360_core` plus `mart_subscriber_health_scorecard`
- open Jenkins at [http://localhost:8081](http://localhost:8081), open the `A1-external-reference` pipeline, click **Build Now**, and confirm the run reads `variants/A1-external-reference/Jenkinsfile` and completes the generated stages
- open the DMM marketplace at [http://localhost:8095](http://localhost:8095) and confirm the A1 silver data product with its `subscriber360_core` and `subscriber_health_scorecard` exposes appears under the telco domain

### A2 Internal Reference

```bash
cd "$GREENFIELD_WORKSPACE/variants/A2-internal-reference"
set -a
source "$FLUID_SECRETS_FILE"
set +a
"$FLUID_CLI" validate contract.fluid.yaml
"$FLUID_CLI" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
"$FLUID_CLI" apply contract.fluid.yaml --mode amend-and-build --build dv2_subscriber360_internal_build --yes --report runtime/apply_report.html
# A2 is a dev-source scenario — same bind-mount flow as A1.
"$FLUID_CLI" generate ci contract.fluid.yaml --system jenkins --install-mode dev-source --out Jenkinsfile
git add .
git commit -m "Refresh internal-reference silver variant"
"$FLUID_CLI" publish contract.fluid.yaml --target datamesh-manager
```

Validation:

- open Airflow at [http://localhost:8085](http://localhost:8085) and confirm DAG `telco_subscriber360_internal`
- run `(cd "$LAB_REPO" && task dbt:docs:refresh SCENARIO=A2)` then open [http://localhost:8086](http://localhost:8086) and confirm `mart_subscriber360_core` plus `mart_subscriber_health_scorecard`
- open Jenkins at [http://localhost:8081](http://localhost:8081), open the `A2-internal-reference` pipeline, click **Build Now**, and confirm the run reads `variants/A2-internal-reference/Jenkinsfile` and completes the generated stages
- open the DMM marketplace at [http://localhost:8095](http://localhost:8095) and confirm the A2 silver data product with its `subscriber360_core` and `subscriber_health_scorecard` exposes appears under the telco domain

## Coming Soon — AI Forge Variants (B1, B2)

Two additional scenarios are staged for a future release of this lab:

- **B1** — AI forge with external references (references existing dbt/Airflow assets)
- **B2** — AI forge with generated assets (generates dbt/Airflow assets in-workspace)

Golden contracts and workspace scaffolds are already parked under `fluid/fixtures/forge-golden/` and `fluid/fixtures/workspaces/path-b-ai-telco-silver-import-demo/`, and the forge-cli gaps blocking them (`fluid init --yes`, `fluid forge --context`, fragment-first build IDs) are tracked in [FLUID Gap Register](fluid-gap-register.md). You may also see a `B1-subscriber360-external` pipeline auto-provisioned in Jenkins — it's staged for that future release.

## Jenkins SCM Handoff

After each `fluid generate ci` step:

1. commit the generated `Jenkinsfile` in the workspace repo on disk
2. open the matching pipeline in Jenkins (`A1-external-reference` or `A2-internal-reference`) and click **Build Now**

The pipelines are auto-provisioned by `task jenkins:up` via CasC JobDSL. Their SCM source is the local workspace repo mounted read-only at `/workspace/gitlab/` — `git push` is not required.

Use [Jenkins SCM Handoff](jenkins-scm-handoff.md) for the expected script paths and job model.

## Related Docs

- [Launchpad Common](launchpad-common.md)
- [Launchpad Recovery](launchpad-recovery.md)
- [Plan Verification Checklist](plan-verification-checklist.md)
- [Scenario Validation Matrix](scenario-validation-matrix.md)
- [Jenkins SCM Handoff](jenkins-scm-handoff.md)
- [Variant Playbook (Windows)](variant-playbook-windows.md)
