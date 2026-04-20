# Dev Source Launchpad (Mac)

Use this when you want one uninterrupted Mac path for the editable `forge-cli` development flow.

This launchpad is meant for community contributors working on [`forge-cli`](https://github.com/Agentics-Rising/forge-cli). Use it when you want to change CLI behavior locally, test those source changes, and iterate before the release-demo path.

All shared setup, reset, platform bring-up, data prep, credentials, and browser links live in [Launchpad Common](launchpad-common.md).

> [!CAUTION]
> This path is for contributors working on [`forge-cli`](https://github.com/Agentics-Rising/forge-cli). Expect editable local source changes, and use only disposable sandbox infrastructure because the runbook includes destructive resets for both the local demo stacks and the Snowflake demo database.

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

## Dev-Source Variables

```bash
export FORGE_CLI_REPO="${FORGE_CLI_REPO:-$LOCAL_REPOS_DIR/forge-cli}"
export FLUID_DEV_VENV="$LAB_REPO/.venv.fluid-dev"
export FLUID_DEV_BIN="$FLUID_DEV_VENV/bin/fluid"
```

If you use a separate `forge-cli` worktree, override `FORGE_CLI_REPO` before bootstrapping the runtime.

## Bootstrap Source Runtime

```bash
python3 -m venv "$FLUID_DEV_VENV"
"$FLUID_DEV_VENV/bin/pip" install --upgrade pip
"$FLUID_DEV_VENV/bin/pip" install -e "$FORGE_CLI_REPO"
git -C "$FORGE_CLI_REPO" branch --show-current
git -C "$FORGE_CLI_REPO" status --short --branch
"$FLUID_DEV_BIN" version
```

## Mandatory Plan Verification Gate

Every variant in both workspaces must stop after `plan`.

Use this exact gate:

```bash
"$FLUID_DEV_BIN" validate contract.fluid.yaml
"$FLUID_DEV_BIN" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
```

Then review:

- [Plan Verification Checklist](plan-verification-checklist.md)

Do not run `"$FLUID_DEV_BIN" apply ... --build` until the checklist is complete and the plan is confirmed.

## Scenario Selector

Use the shared scenario names below when you test contributor changes in `forge-cli`.

| Scenario | Intent | Root | Contract Or Target | dbt/Airflow Mode | Contributor Focus |
| --- | --- | --- | --- | --- | --- |
| Bronze | Upstream lineage anchor | `$LAB_REPO` | `fluid/contracts/telco_seed_billing/`, `.../telco_seed_party/`, `.../telco_seed_usage/` (one contract each) | No dbt/Airflow/Jenkins assets | schema, parser, publish, lineage anchor |
| A1 | External-reference silver contract | `$GREENFIELD_WORKSPACE` | `variants/A1-external-reference/contract.fluid.yaml` | referenced dbt + referenced Airflow | reference resolution, plan/apply, publish |
| A2 | Internal-reference silver contract | `$GREENFIELD_WORKSPACE` | `variants/A2-internal-reference/contract.fluid.yaml` | packaged dbt + packaged Airflow | packaging, plan/apply, publish |
| B1 | AI forge with external references | `$EXISTING_DBT_WORKSPACE` | `variants/B1-ai-reference-external/subscriber360-external` | referenced dbt + referenced Airflow | forge interview, reference resolution |
| B2 | AI forge with generated assets | `$EXISTING_DBT_WORKSPACE` | `variants/B2-ai-generate-in-workspace/subscriber360-generated` | generated dbt + generated Airflow | generation, transformation generation, schedule generation |

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
  "$FLUID_DEV_BIN" validate "$contract"
  "$FLUID_DEV_BIN" plan "$contract" --out "fluid/contracts/telco_seed_${domain}/runtime/plan.json" --html
  "$FLUID_DEV_BIN" publish "$contract" --catalog datamesh-manager
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
set -a
source "$FLUID_SECRETS_FILE"
set +a
"$FLUID_DEV_BIN" validate contract.fluid.yaml
"$FLUID_DEV_BIN" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
"$FLUID_DEV_BIN" apply contract.fluid.yaml --build dv2_subscriber360_reference_build --yes --report runtime/apply_report.html
"$FLUID_DEV_BIN" generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Refresh external-reference silver variant"
git push
"$FLUID_DEV_BIN" publish contract.fluid.yaml --catalog datamesh-manager
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
"$FLUID_DEV_BIN" validate contract.fluid.yaml
"$FLUID_DEV_BIN" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
"$FLUID_DEV_BIN" apply contract.fluid.yaml --build dv2_subscriber360_internal_build --yes --report runtime/apply_report.html
"$FLUID_DEV_BIN" generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Refresh internal-reference silver variant"
git push
"$FLUID_DEV_BIN" publish contract.fluid.yaml --catalog datamesh-manager
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
set -a
source "$FLUID_SECRETS_FILE"
set +a
cat ../../prompts/ai-reference-external.md
"$FLUID_DEV_BIN" init subscriber360-external --provider snowflake --yes
cd subscriber360-external

# --- Demo mode: replay the captured golden contract (deterministic) ---
cp "$LAB_REPO/fluid/fixtures/forge-golden/B1-ai-reference-external/contract.fluid.yaml" contract.fluid.yaml

# --- Live mode (alternative): uncomment to call the real LLM instead ---
# "$FLUID_DEV_BIN" forge --provider snowflake --domain telco --target-dir .

"$FLUID_DEV_BIN" validate contract.fluid.yaml
"$FLUID_DEV_BIN" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
BUILD_ID="$(python3 "$LAB_REPO/scripts/get_first_build_id.py" contract.fluid.yaml)"
"$FLUID_DEV_BIN" apply contract.fluid.yaml --build "$BUILD_ID" --yes --report runtime/apply_report.html
"$FLUID_DEV_BIN" generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Generate AI external-reference silver variant"
git push
"$FLUID_DEV_BIN" publish contract.fluid.yaml --catalog datamesh-manager
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
"$FLUID_DEV_BIN" init subscriber360-generated --provider snowflake --yes
cd subscriber360-generated

# --- Demo mode: replay the captured golden contract (deterministic) ---
cp "$LAB_REPO/fluid/fixtures/forge-golden/B2-ai-generate-in-workspace/contract.fluid.yaml" contract.fluid.yaml

# --- Live mode (alternative): uncomment to call the real LLM instead ---
# "$FLUID_DEV_BIN" forge --provider snowflake --domain telco --target-dir .

"$FLUID_DEV_BIN" validate contract.fluid.yaml
"$FLUID_DEV_BIN" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
"$FLUID_DEV_BIN" generate transformation contract.fluid.yaml --engine dbt -o generated/dbt --overwrite
"$FLUID_DEV_BIN" generate schedule contract.fluid.yaml --scheduler airflow -o generated/airflow --overwrite
BUILD_ID="$(python3 "$LAB_REPO/scripts/get_first_build_id.py" contract.fluid.yaml)"
"$FLUID_DEV_BIN" apply contract.fluid.yaml --build "$BUILD_ID" --yes --report runtime/apply_report.html
"$FLUID_DEV_BIN" generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Generate AI in-workspace silver variant"
git push
"$FLUID_DEV_BIN" publish contract.fluid.yaml --catalog datamesh-manager
```

Validation:

- open Airflow at [http://localhost:8085](http://localhost:8085) and confirm the generated DAG from `generated/airflow` appears with an ID derived from the generated contract ID
- run `(cd "$LAB_REPO" && task dbt:docs:refresh SCENARIO=B2)` then open [http://localhost:8086](http://localhost:8086) and confirm `mart_subscriber360_core` plus `mart_subscriber_health_scorecard`
- open Jenkins at [http://localhost:8081](http://localhost:8081); B2 is not auto-provisioned (the Jenkinsfile only exists after `fluid generate ci`) — if you want the pipeline in the UI, add a JobDSL entry to `jenkins/casc/jenkins.yaml` pointing at `variants/B2-ai-generate-in-workspace/subscriber360-generated/Jenkinsfile` and rerun `task jenkins:up`
- open the DMM marketplace at [http://localhost:8095](http://localhost:8095) and confirm the B2 silver data product with its `subscriber360_core` and `subscriber_health_scorecard` exposes appears under the telco domain

## Jenkins SCM Handoff

After each `generate ci` step:

1. commit the generated `Jenkinsfile` in the workspace repo on disk
2. open the matching pipeline in Jenkins (`A1-external-reference`, `A2-internal-reference`, `B1-subscriber360-external`) and click **Build Now**

The pipelines are auto-provisioned by `task jenkins:up` via CasC JobDSL. Their SCM source is the local workspace repo mounted read-only at `/workspace/gitlab/` — `git push` is not required.

Use [Jenkins SCM Handoff](jenkins-scm-handoff.md) for the expected script paths and job model.

## Recovery Appendix

Quick resets for the failures that happen most often on a live rehearsal. Each block is self-contained — pick the row that matches what broke.

### DMM publish succeeded but nothing appears at `http://localhost:8095`

Usually the API key in `runtime/generated/fluid.local.env` is stale or the catalog stack was never bootstrapped. Refresh both:

```bash
cd "$LAB_REPO"
task catalogs:up
task catalogs:bootstrap
# then re-run the failing `fluid publish` command
```

If the UI still shows nothing, do a clean catalog reset:

```bash
cd "$LAB_REPO"
task catalogs:reset
task catalogs:up
task catalogs:bootstrap
# then re-run every `fluid publish` from the start of your scenario
```

### Jenkins did not pick up the Jenkinsfile

The CasC pipelines read from `/workspace/gitlab/` (the workspace folder on disk, not GitLab remote). Reprovision so CasC rescans:

```bash
cd "$LAB_REPO"
task jenkins:down
task jenkins:up
```

Then reopen [http://localhost:8081](http://localhost:8081) and click **Scan Multibranch Pipeline Now** on the affected job.

### `fluid apply` failed partway through (auth, role, or adapter error)

Reload Snowflake secrets into the current shell and retry the same `apply` command — the build is idempotent for the demo-scoped schema:

```bash
cd "$WORKSPACE_PATH_FROM_YOUR_SCENARIO"
set -a
source "$FLUID_SECRETS_FILE"
set +a
"$FLUID_DEV_BIN" apply contract.fluid.yaml --build "$BUILD_ID" --yes --report runtime/apply_report.html
```

If auth is the root cause, open `runtime/generated/fluid.local.env` and confirm the `SNOWFLAKE_*` values are current; the Docker seed tasks read `.env` instead, so the two files can drift.

### Full reset (when you need a guaranteed clean rerun)

Runs the destructive reset from [Launchpad Common](launchpad-common.md#start-clean-first) and the off-stage data prep afterwards:

```bash
cd "$LAB_REPO"
python3 scripts/reset_demo_state.py --lab-repo "$LAB_REPO" --greenfield-workspace "$GREENFIELD_WORKSPACE" --existing-workspace "$EXISTING_DBT_WORKSPACE" --yes
task down && task jenkins:down && task catalogs:reset
task up && task jenkins:up && task catalogs:up && task catalogs:bootstrap
task seed:reset:confirm && task seed:generate && task seed:load && task seed:verify
task metadata:apply && task metadata:verify
```

Then restart this launchpad from **Bootstrap Source Runtime**.

## Related Docs

- [Launchpad Common](launchpad-common.md)
- [Plan Verification Checklist](plan-verification-checklist.md)
- [Scenario Validation Matrix](scenario-validation-matrix.md)
- [Jenkins SCM Handoff](jenkins-scm-handoff.md)
- [Dev Source Launchpad (Windows)](dev-source-launchpad-windows.md)
- Workspace A root: `gitlab/path-a-telco-silver-product-demo`
- Workspace B root: `gitlab/path-b-ai-telco-silver-import-demo`
