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

Then review [Plan Verification Checklist](plan-verification-checklist.md). Do not run `"$FLUID_CLI" apply --build` until the checklist is complete and the plan is confirmed.

## Scenario Vocabulary

- **Bronze** — upstream lineage anchor, three contracts: `telco_seed_billing`, `telco_seed_party`, `telco_seed_usage`
- **A1** — external-reference silver contract
- **A2** — internal-reference silver contract
- **B1** — AI forge with external references
- **B2** — AI forge with generated assets

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
  "$FLUID_CLI" publish "$contract" --catalog datamesh-manager
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
"$FLUID_CLI" apply contract.fluid.yaml --build dv2_subscriber360_reference_build --yes --report runtime/apply_report.html
"$FLUID_CLI" generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Refresh external-reference silver variant"
"$FLUID_CLI" publish contract.fluid.yaml --catalog datamesh-manager
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
"$FLUID_CLI" apply contract.fluid.yaml --build dv2_subscriber360_internal_build --yes --report runtime/apply_report.html
"$FLUID_CLI" generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Refresh internal-reference silver variant"
"$FLUID_CLI" publish contract.fluid.yaml --catalog datamesh-manager
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
"$FLUID_CLI" init subscriber360-external --provider snowflake --yes
cd subscriber360-external

# --- Demo mode: replay the captured golden contract (deterministic) ---
cp "$LAB_REPO/fluid/fixtures/forge-golden/B1-ai-reference-external/contract.fluid.yaml" contract.fluid.yaml

# --- Live mode (alternative): uncomment to call the real LLM instead ---
# "$FLUID_CLI" forge --provider snowflake --domain telco --target-dir .

"$FLUID_CLI" validate contract.fluid.yaml
"$FLUID_CLI" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
BUILD_ID="$(python3 "$LAB_REPO/scripts/get_first_build_id.py" contract.fluid.yaml)"
"$FLUID_CLI" apply contract.fluid.yaml --build "$BUILD_ID" --yes --report runtime/apply_report.html
"$FLUID_CLI" generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Generate AI external-reference silver variant"
"$FLUID_CLI" publish contract.fluid.yaml --catalog datamesh-manager
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
"$FLUID_CLI" init subscriber360-generated --provider snowflake --yes
cd subscriber360-generated

# --- Demo mode: replay the captured golden contract (deterministic) ---
cp "$LAB_REPO/fluid/fixtures/forge-golden/B2-ai-generate-in-workspace/contract.fluid.yaml" contract.fluid.yaml

# --- Live mode (alternative): uncomment to call the real LLM instead ---
# "$FLUID_CLI" forge --provider snowflake --domain telco --target-dir .

"$FLUID_CLI" validate contract.fluid.yaml
"$FLUID_CLI" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
"$FLUID_CLI" generate transformation contract.fluid.yaml --engine dbt -o generated/dbt --overwrite
"$FLUID_CLI" generate schedule contract.fluid.yaml --scheduler airflow -o generated/airflow --overwrite
BUILD_ID="$(python3 "$LAB_REPO/scripts/get_first_build_id.py" contract.fluid.yaml)"
"$FLUID_CLI" apply contract.fluid.yaml --build "$BUILD_ID" --yes --report runtime/apply_report.html
"$FLUID_CLI" generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Generate AI in-workspace silver variant"
"$FLUID_CLI" publish contract.fluid.yaml --catalog datamesh-manager
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
