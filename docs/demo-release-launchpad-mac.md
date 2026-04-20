# Demo Release Launchpad (Mac)

Use this when you want one uninterrupted Mac path for the final audience demo.

This launchpad is meant for testing and demoing inside a safe sandbox environment. Use it when you want to exercise the released `data-product-forge` package without changing `forge-cli` source code.

All shared setup, reset, platform bring-up, data prep, credentials, and browser links live in [Launchpad Common](launchpad-common.md).

> [!CAUTION]
> Use this launchpad only against a safe sandbox environment. The runbook includes destructive reset steps for local stacks and the Snowflake demo database before the source-load path is rebuilt.

## Start Clean First

If you want a fully reproducible rerun, start with the shared reset flow before anything else:

```bash
cd "$LAB_REPO"
./scripts/setup_mac_launchpad.sh --force
source runtime/generated/launchpad.local.sh
python3 scripts/reset_demo_state.py --lab-repo "$LAB_REPO" --greenfield-workspace "$GREENFIELD_WORKSPACE" --existing-workspace "$EXISTING_DBT_WORKSPACE" --yes
task down
task jenkins:down
task catalogs:reset
```

Then return to [Launchpad Common](launchpad-common.md) and continue from step 2.

## Before You Start

1. Complete steps 1 through 8 in [Launchpad Common](launchpad-common.md).
2. Start this page only after you reach step 8 there.

## Demo-Release Variable

```bash
export FLUID_DEMO_PACKAGE_SPEC="${FLUID_DEMO_PACKAGE_SPEC:-data-product-forge}"
```

## Bootstrap Release Runtime In Both Workspaces

### Workspace A: Ready-Made Variants

```bash
cd "$GREENFIELD_WORKSPACE"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ "$FLUID_DEMO_PACKAGE_SPEC"
fluid version
```

### Workspace B: AI Variants

```bash
cd "$EXISTING_DBT_WORKSPACE"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ "$FLUID_DEMO_PACKAGE_SPEC"
fluid version
```

## Mandatory Plan Verification Gate

Every variant in both workspaces must stop after `fluid plan`.

Use this exact gate:

```bash
fluid validate contract.fluid.yaml
fluid plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
```

Then review:

- [Plan Verification Checklist](plan-verification-checklist.md)

Do not run `fluid apply --build` until the checklist is complete and the plan is confirmed.

## Scenario Names Used In This Launchpad

Use the same scenario names as the dev-source track:

- **Bronze** upstream lineage anchor — three contracts: `telco_seed_billing`, `telco_seed_party`, `telco_seed_usage`
- **A1** external-reference silver contract
- **A2** internal-reference silver contract
- **B1** AI forge with external references
- **B2** AI forge with generated assets

Use [Scenario Validation Matrix](scenario-validation-matrix.md) for the exact contract paths, dbt roots, DAG paths, DAG IDs, Jenkinsfile paths, and expose names.

## Bronze Anchor Scenario

Bronze is published as **three contracts**, one per subject area: billing, party, and usage. They are the upstream lineage anchors for the silver variants.

Load Snowflake secrets once, then validate, plan, and publish each contract:

```bash
cd "$LAB_REPO"
source "$GREENFIELD_WORKSPACE/.venv/bin/activate"
set -a
source "$FLUID_SECRETS_FILE"
set +a

for domain in billing party usage; do
  contract="fluid/contracts/telco_seed_${domain}/contract.fluid.yaml"
  fluid validate "$contract"
  fluid plan "$contract" --out "fluid/contracts/telco_seed_${domain}/runtime/plan.json" --html
  fluid publish "$contract" --catalog datamesh-manager
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

### A1 External Reference

```bash
cd "$GREENFIELD_WORKSPACE/variants/A1-external-reference"
source "$GREENFIELD_WORKSPACE/.venv/bin/activate"
set -a
source "$FLUID_SECRETS_FILE"
set +a
fluid validate contract.fluid.yaml
fluid plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
fluid apply contract.fluid.yaml --build dv2_subscriber360_reference_build --yes --report runtime/apply_report.html
fluid generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Refresh external-reference silver variant"
git push
fluid publish contract.fluid.yaml --catalog datamesh-manager
```

Validation:

- open Airflow at [http://localhost:8085](http://localhost:8085) and confirm DAG `telco_subscriber360_reference`
- run `(cd "$LAB_REPO" && task dbt:docs:refresh SCENARIO=A1)` then open [http://localhost:8086](http://localhost:8086) and confirm `mart_subscriber360_core` plus `mart_subscriber_health_scorecard`
- open Jenkins at [http://localhost:8081](http://localhost:8081), open the `A1-external-reference` pipeline, click **Build Now**, and confirm the run reads `variants/A1-external-reference/Jenkinsfile` and completes the generated stages
- open the DMM marketplace at [http://localhost:8095](http://localhost:8095) and confirm the A1 silver data product with its `subscriber360_core` and `subscriber_health_scorecard` exposes appears under the telco domain

### A2 Internal Reference

```bash
cd "$GREENFIELD_WORKSPACE/variants/A2-internal-reference"
source "$GREENFIELD_WORKSPACE/.venv/bin/activate"
set -a
source "$FLUID_SECRETS_FILE"
set +a
fluid validate contract.fluid.yaml
fluid plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
fluid apply contract.fluid.yaml --build dv2_subscriber360_internal_build --yes --report runtime/apply_report.html
fluid generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Refresh internal-reference silver variant"
git push
fluid publish contract.fluid.yaml --catalog datamesh-manager
```

Validation:

- open Airflow at [http://localhost:8085](http://localhost:8085) and confirm DAG `telco_subscriber360_internal`
- run `(cd "$LAB_REPO" && task dbt:docs:refresh SCENARIO=A2)` then open [http://localhost:8086](http://localhost:8086) and confirm `mart_subscriber360_core` plus `mart_subscriber_health_scorecard`
- open Jenkins at [http://localhost:8081](http://localhost:8081), open the `A2-internal-reference` pipeline, click **Build Now**, and confirm the run reads `variants/A2-internal-reference/Jenkinsfile` and completes the generated stages
- open the DMM marketplace at [http://localhost:8095](http://localhost:8095) and confirm the A2 silver data product with its `subscriber360_core` and `subscriber_health_scorecard` exposes appears under the telco domain

## Workspace B: AI Variants

The AI-created workspaces are expected to land here:

```text
$EXISTING_DBT_WORKSPACE/variants/B1-ai-reference-external/subscriber360-external
$EXISTING_DBT_WORKSPACE/variants/B2-ai-generate-in-workspace/subscriber360-generated
```

### B1 AI Forge + External References

There are two ways to run B1 — pick one based on who is watching.

**Demo mode (recommended for presentations):** copy the golden contract that `fluid forge` produced during an off-stage capture, so the on-stage flow is deterministic. See [`fluid/fixtures/forge-golden/README.md`](../fluid/fixtures/forge-golden/README.md) for how the golden is captured and refreshed.

**Live mode (for forge-cli contributors):** call the real LLM so you can iterate on prompts, providers, or templates.

```bash
cd "$EXISTING_DBT_WORKSPACE/variants/B1-ai-reference-external"
source "$EXISTING_DBT_WORKSPACE/.venv/bin/activate"
set -a
source "$FLUID_SECRETS_FILE"
set +a
cat ../../prompts/ai-reference-external.md
fluid init subscriber360-external --provider snowflake --yes
cd subscriber360-external

# --- Demo mode: replay the captured golden contract (deterministic) ---
cp "$LAB_REPO/fluid/fixtures/forge-golden/B1-ai-reference-external/contract.fluid.yaml" contract.fluid.yaml

# --- Live mode (alternative): uncomment to call the real LLM instead ---
# fluid forge --provider snowflake --domain telco --target-dir .

fluid validate contract.fluid.yaml
fluid plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
BUILD_ID="$(python3 "$LAB_REPO/scripts/get_first_build_id.py" contract.fluid.yaml)"
fluid apply contract.fluid.yaml --build "$BUILD_ID" --yes --report runtime/apply_report.html
fluid generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Generate AI external-reference silver variant"
git push
fluid publish contract.fluid.yaml --catalog datamesh-manager
```

Validation:

- open Airflow at [http://localhost:8085](http://localhost:8085) and confirm DAG `telco_subscriber360_reference`
- run `(cd "$LAB_REPO" && task dbt:docs:refresh SCENARIO=B1)` then open [http://localhost:8086](http://localhost:8086) and confirm `mart_subscriber360_core` plus `mart_subscriber_health_scorecard`
- open Jenkins at [http://localhost:8081](http://localhost:8081), open the `B1-subscriber360-external` pipeline, click **Build Now**, and confirm the run reads `variants/B1-ai-reference-external/subscriber360-external/Jenkinsfile` and completes the generated stages
- open the DMM marketplace at [http://localhost:8095](http://localhost:8095) and confirm the `subscriber360_core` and `subscriber_health_scorecard` exposes appear under the silver data product

### B2 AI Forge + Generated Assets

There are two ways to run B2 — pick one based on who is watching.

**Demo mode (recommended for presentations):** copy the golden contract that `fluid forge` produced during an off-stage capture, so the on-stage flow is deterministic. If the golden folder also contains pre-generated `generated/dbt/` and `generated/airflow/` assets, the copy covers them too and the `generate transformation`/`generate schedule` lines become no-ops you can keep or remove. See [`fluid/fixtures/forge-golden/README.md`](../fluid/fixtures/forge-golden/README.md) for how the golden is captured and refreshed.

**Live mode (for forge-cli contributors):** call the real LLM so you can iterate on prompts, providers, or templates.

```bash
cd "$EXISTING_DBT_WORKSPACE/variants/B2-ai-generate-in-workspace"
source "$EXISTING_DBT_WORKSPACE/.venv/bin/activate"
set -a
source "$FLUID_SECRETS_FILE"
set +a
cat ../../prompts/ai-generate-in-workspace.md
fluid init subscriber360-generated --provider snowflake --yes
cd subscriber360-generated

# --- Demo mode: replay the captured golden contract (deterministic) ---
cp "$LAB_REPO/fluid/fixtures/forge-golden/B2-ai-generate-in-workspace/contract.fluid.yaml" contract.fluid.yaml

# --- Live mode (alternative): uncomment to call the real LLM instead ---
# fluid forge --provider snowflake --domain telco --target-dir .

fluid validate contract.fluid.yaml
fluid plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
fluid generate transformation contract.fluid.yaml --engine dbt -o generated/dbt --overwrite
fluid generate schedule contract.fluid.yaml --scheduler airflow -o generated/airflow --overwrite
BUILD_ID="$(python3 "$LAB_REPO/scripts/get_first_build_id.py" contract.fluid.yaml)"
fluid apply contract.fluid.yaml --build "$BUILD_ID" --yes --report runtime/apply_report.html
fluid generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Generate AI in-workspace silver variant"
git push
fluid publish contract.fluid.yaml --catalog datamesh-manager
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
- [Plan Verification Checklist](plan-verification-checklist.md)
- [Scenario Validation Matrix](scenario-validation-matrix.md)
- [Jenkins SCM Handoff](jenkins-scm-handoff.md)
- [Demo Release Launchpad (Windows)](demo-release-launchpad-windows.md)
- Workspace A root: `gitlab/path-a-telco-silver-product-demo`
- Workspace B root: `gitlab/path-b-ai-telco-silver-import-demo`
