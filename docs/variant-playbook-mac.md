# Variant Playbook (Mac)

Shared Bronze / A1 / A2 / B1 / B2 commands for both the demo-release and dev-source tracks on macOS. The track launchpad sets up the FLUID runtime and the `FLUID_CLI` variable; this playbook runs the variants.

## Before You Start

Your track launchpad must have already:

- bootstrapped a FLUID runtime (venv in each workspace for demo-release; a single lab-level venv for dev-source)
- exported `FLUID_CLI` — either `fluid` (demo-release, with the active workspace venv) or `"$FLUID_DEV_BIN"` (dev-source)
- loaded `$LAB_REPO`, `$GREENFIELD_WORKSPACE`, `$EXISTING_DBT_WORKSPACE`, `$FLUID_SECRETS_FILE`

If you need to re-activate a demo-release workspace venv between variant groups, `source "$GREENFIELD_WORKSPACE/.venv/bin/activate"` for A1/A2 or `source "$EXISTING_DBT_WORKSPACE/.venv/bin/activate"` for B1/B2. Dev-source uses a single `$FLUID_DEV_BIN` across all variants.

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
- **B1** — AI forge with external references
- **B2** — AI forge with generated assets

### Install-Mode Partition (Jenkins CI surface)

Each variant's generated `Jenkinsfile` is pinned to one of two install modes — chosen when you run `fluid generate ci`. This determines how the Jenkins container installs `fluid` at build time:

| Variant | `--install-mode` | Where Jenkins gets `fluid` | Demo track |
|---|---|---|---|
| **A1** | `dev-source` | Bind-mounted `/forge-cli-src` in the Jenkins container (see [dev-source-launchpad-mac.md](dev-source-launchpad-mac.md)) | lab iteration — contributors testing forge-cli changes against real A1 contract |
| **A2** | `dev-source` | Same bind mount as A1 | lab iteration |
| **B1** | `pypi` | `pip install data-product-forge` from **TestPyPI** via Jenkins build-params (`FLUID_PIP_INDEX_URL=https://test.pypi.org/simple/`, `FLUID_ALLOW_PRERELEASE=true`) | demo-release showcase — pre-release pilot track |
| **B2** | `pypi` | `pip install data-product-forge` from stable PyPI. Zero overrides. | production — what a customer team actually ships |

Bronze contracts (`telco_seed_*`) don't publish Jenkinsfiles today; they're published to the catalog directly via `fluid publish` without a CI step.

The `pypi` vs `dev-source` choice is part of `fluid generate ci --install-mode` — it lives in the Jenkinsfile itself. TestPyPI is NOT a separate mode; it's a **build-time override** inside `pypi` mode, exposed as Jenkins UI parameters (`FLUID_PIP_INDEX_URL`, `FLUID_PIP_EXTRA_INDEX_URL`, `FLUID_ALLOW_PRERELEASE`, `FLUID_PACKAGE_SPEC`). B1 demos flip those; B2 leaves them at their production defaults.

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

## Workspace B: AI Variants

Demo-release only — activate Workspace B's venv before running B1 or B2:

```bash
source "$EXISTING_DBT_WORKSPACE/.venv/bin/activate"
```

The AI-created workspaces are expected to land here:

```text
$EXISTING_DBT_WORKSPACE/variants/B1-ai-reference-external/subscriber360-external
$EXISTING_DBT_WORKSPACE/variants/B2-ai-generate-in-workspace/subscriber360-generated
```

### B1 AI Forge + External References

Two ways to run B1 — pick one based on who is watching.

**Demo mode (recommended for presentations):** copy the golden contract that `fluid forge` produced during an off-stage capture, so the on-stage flow is deterministic. See [`fluid/fixtures/forge-golden/README.md`](../fluid/fixtures/forge-golden/README.md) for how the golden is captured and refreshed.

**Live mode (for forge-cli contributors):** call the real LLM so you can iterate on prompts, providers, or templates.

```bash
cd "$EXISTING_DBT_WORKSPACE/variants/B1-ai-reference-external"
set -a
source "$FLUID_SECRETS_FILE"
set +a
cat ../../prompts/ai-reference-external.md
# `fluid init NAME --yes` still blocks on an interactive mode prompt in
# data-product-forge 0.8.0a1 — see FLUID Gap Register. `--blank` is the
# documented workaround; the contract will be overwritten by the golden below.
"$FLUID_CLI" init subscriber360-external --blank --provider snowflake --yes
cd subscriber360-external

# --- Demo mode: replay the captured golden contract (deterministic) ---
cp "$LAB_REPO/fluid/fixtures/forge-golden/B1-ai-reference-external/contract.fluid.yaml" contract.fluid.yaml

# --- Live mode (alternative): uncomment to call the real LLM instead ---
# "$FLUID_CLI" forge --provider snowflake --domain telco --target-dir .

"$FLUID_CLI" validate contract.fluid.yaml
"$FLUID_CLI" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
BUILD_ID="$(python3 "$LAB_REPO/scripts/get_first_build_id.py" contract.fluid.yaml)"
"$FLUID_CLI" apply contract.fluid.yaml --mode amend-and-build --build "$BUILD_ID" --yes --report runtime/apply_report.html
# B1 is an AI-forge demo scenario — Jenkinsfile installs fluid from PyPI
# (default --install-mode pypi). For the TestPyPI-backed demo track, the
# Jenkins Build-With-Parameters dialog picks up:
#     FLUID_PIP_INDEX_URL        = https://test.pypi.org/simple/
#     FLUID_PIP_EXTRA_INDEX_URL  = https://pypi.org/simple/
#     FLUID_ALLOW_PRERELEASE     = true
# (No flag needed on `generate ci` — pypi is the default mode.)
"$FLUID_CLI" generate ci contract.fluid.yaml --system jenkins --install-mode pypi --out Jenkinsfile
git add .
git commit -m "Generate AI external-reference silver variant"
"$FLUID_CLI" publish contract.fluid.yaml --target datamesh-manager
```

Validation:

- open Airflow at [http://localhost:8085](http://localhost:8085) and confirm DAG `telco_subscriber360_reference`
- run `(cd "$LAB_REPO" && task dbt:docs:refresh SCENARIO=B1)` then open [http://localhost:8086](http://localhost:8086) and confirm `mart_subscriber360_core` plus `mart_subscriber_health_scorecard`
- open Jenkins at [http://localhost:8081](http://localhost:8081), open the `B1-subscriber360-external` pipeline, click **Build Now**, and confirm the run reads `variants/B1-ai-reference-external/subscriber360-external/Jenkinsfile` and completes the generated stages
- open the DMM marketplace at [http://localhost:8095](http://localhost:8095) and confirm the `subscriber360_core` and `subscriber_health_scorecard` exposes appear under the silver data product

### B2 AI Forge + Generated Assets

Same two-mode pattern as B1. Demo mode copies the golden B2 contract; live mode calls the real LLM.

```bash
cd "$EXISTING_DBT_WORKSPACE/variants/B2-ai-generate-in-workspace"
set -a
source "$FLUID_SECRETS_FILE"
set +a
cat ../../prompts/ai-generate-in-workspace.md
# Same `--blank` workaround as B1 — see FLUID Gap Register entry for
# `fluid init --yes` blocking on interactive mode selection in 0.8.0a1.
"$FLUID_CLI" init subscriber360-generated --blank --provider snowflake --yes
cd subscriber360-generated

# --- Demo mode: replay the captured golden bundle (deterministic).
#     The bundle ships contract.fluid.yaml plus pre-generated generated/dbt/
#     and generated/airflow/, so the `generate transformation` / `generate
#     schedule` lines below are no-ops against a fresh copy. ---
cp -R "$LAB_REPO/fluid/fixtures/forge-golden/B2-ai-generate-in-workspace/." ./

# --- Live mode (alternative): uncomment to call the real LLM instead ---
# "$FLUID_CLI" forge --provider snowflake --domain telco --target-dir .

"$FLUID_CLI" validate contract.fluid.yaml
"$FLUID_CLI" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
# Generated assets already exist under generated/dbt and generated/airflow when
# demo mode ran; these commands are the live-mode equivalents for that step.
"$FLUID_CLI" generate transformation contract.fluid.yaml --engine dbt -o generated/dbt --overwrite
"$FLUID_CLI" generate schedule contract.fluid.yaml --scheduler airflow -o generated/airflow --overwrite
BUILD_ID="$(python3 "$LAB_REPO/scripts/get_first_build_id.py" contract.fluid.yaml)"
"$FLUID_CLI" apply contract.fluid.yaml --mode amend-and-build --build "$BUILD_ID" --yes --report runtime/apply_report.html
# B2 is the production-facing AI-forge scenario — Jenkinsfile installs fluid
# from stable PyPI with ZERO overrides. This is what a real customer team
# gets after running `fluid forge` and committing the result.
"$FLUID_CLI" generate ci contract.fluid.yaml --system jenkins --install-mode pypi --out Jenkinsfile
git add .
git commit -m "Generate AI in-workspace silver variant"
"$FLUID_CLI" publish contract.fluid.yaml --target datamesh-manager
```

Validation:

- open Airflow at [http://localhost:8085](http://localhost:8085) and confirm the generated DAG from `generated/airflow` appears with an ID derived from the generated contract ID
- run `(cd "$LAB_REPO" && task dbt:docs:refresh SCENARIO=B2)` then open [http://localhost:8086](http://localhost:8086) and confirm `mart_subscriber360_core` plus `mart_subscriber_health_scorecard`
- open Jenkins at [http://localhost:8081](http://localhost:8081); B2 is not auto-provisioned (the Jenkinsfile only exists after `fluid generate ci`) — if you want the pipeline in the UI, add a JobDSL entry to `jenkins/casc/jenkins.yaml` pointing at `variants/B2-ai-generate-in-workspace/subscriber360-generated/Jenkinsfile` and rerun `task jenkins:up`
- open the DMM marketplace at [http://localhost:8095](http://localhost:8095) and confirm the B2 silver data product with its `subscriber360_core` and `subscriber_health_scorecard` exposes appears under the telco domain

## Jenkins SCM Handoff

After each `fluid generate ci` step:

1. commit the generated `Jenkinsfile` in the workspace repo on disk
2. open the matching pipeline in Jenkins (`A1-external-reference`, `A2-internal-reference`, `B1-subscriber360-external`) and click **Build Now**

The pipelines are auto-provisioned by `task jenkins:up` via CasC JobDSL. Their SCM source is the local workspace repo mounted read-only at `/workspace/gitlab/` — `git push` is not required.

Use [Jenkins SCM Handoff](jenkins-scm-handoff.md) for the expected script paths and job model.

## Related Docs

- [Launchpad Common](launchpad-common.md)
- [Launchpad Recovery](launchpad-recovery.md)
- [Plan Verification Checklist](plan-verification-checklist.md)
- [Scenario Validation Matrix](scenario-validation-matrix.md)
- [Jenkins SCM Handoff](jenkins-scm-handoff.md)
- [Variant Playbook (Windows)](variant-playbook-windows.md)
