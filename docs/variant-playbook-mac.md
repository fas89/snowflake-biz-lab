# Variant Playbook (Mac)

Shared Bronze, A1, A2, B1, and B2 commands for macOS. Your chosen track launchpad must already have exported `FLUID_CLI`, `FLUID_SECRETS_FILE`, and `JENKINS_INSTALL_MODE`.

## Before You Start

Make sure all of these are true:

- [Launchpad Common](launchpad-common.md) is complete
- `FLUID_CLI` points at the runtime for your chosen track
- `JENKINS_INSTALL_MODE` is set to `dev-source` or `pypi`
- `FLUID_SECRETS_FILE` points at `runtime/generated/fluid.local.env`

## Mandatory Plan Gate

Every scenario stops after `plan` until the plan review is complete:

```bash
"$FLUID_CLI" validate contract.fluid.yaml
"$FLUID_CLI" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
```

Review [Plan Verification Checklist](plan-verification-checklist.md) before you continue to `apply`.

## Bronze

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

Validation:

- all three bronze plans review cleanly
- DMM shows `bronze.telco.billing_v1`, `bronze.telco.party_v1`, and `bronze.telco.usage_v1`
- no Jenkins jobs or Airflow DAGs are expected from Bronze

## A1 External Reference

```bash
cd "$GREENFIELD_WORKSPACE/variants/A1-external-reference"
set -a
source "$FLUID_SECRETS_FILE"
set +a
"$FLUID_CLI" validate contract.fluid.yaml
"$FLUID_CLI" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
"$FLUID_CLI" apply contract.fluid.yaml --mode amend-and-build --build dv2_subscriber360_reference_build --yes --report runtime/apply_report.html
"$FLUID_CLI" generate ci contract.fluid.yaml --system jenkins --install-mode "$JENKINS_INSTALL_MODE" --default-publish-target datamesh-manager --no-verify-strict-default --publish-stage-default --no-publish-include-env --out Jenkinsfile
git status --short -- Jenkinsfile
git add Jenkinsfile
if ! git diff --cached --quiet -- Jenkinsfile; then
  git commit -m "Refresh external-reference silver variant"
else
  echo "Jenkinsfile already committed"
fi
cd "$LAB_REPO"
task jenkins:sync SCENARIO=A1
task jenkins:build SCENARIO=A1
cd "$GREENFIELD_WORKSPACE/variants/A1-external-reference"
rm -rf "$LAB_REPO/airflow/dags/active/current"
"$FLUID_CLI" schedule-sync --scheduler airflow --dags-dir ../../reference-assets/airflow_subscriber360/dags --destination "$LAB_REPO/airflow/dags/active/current"
"$FLUID_CLI" publish contract.fluid.yaml --target datamesh-manager
```

Validation:

- Jenkins now lists `A1-external-reference`; it did not exist before `task jenkins:sync`
- `task jenkins:build SCENARIO=A1` runs the controller build through Jenkins `buildWithParameters` and confirms the pipeline reads `variants/A1-external-reference/Jenkinsfile`
- in the demo-release track, `task jenkins:sync` and `task jenkins:build` automatically carry the package resolved in `runtime/generated/demo-release.env`; do not add manual TestPyPI `--param` flags unless you are deliberately overriding the launchpad
- the A1 Jenkins build should succeed and publish; generate the Jenkinsfile with `--no-verify-strict-default`, `--publish-stage-default`, and `--no-publish-include-env` so the file is emitted with the lab-tuned defaults directly
- those A1 defaults are intentional because the shared Snowflake/dbt reference assets materialize nullable columns that `fluid verify --strict` would otherwise flag as constraint mismatches
- Airflow now lists DAG `telco_subscriber360_reference`; it did not exist before the `schedule-sync` command
- run `cd "$LAB_REPO" && task dbt:docs:refresh SCENARIO=A1`, then confirm dbt docs shows `mart_subscriber360_core` and `mart_subscriber_health_scorecard`
- DMM shows the A1 silver product with `subscriber360_core` and `subscriber_health_scorecard`
- DMM Access agreements show A1 consuming the Bronze `party`, `usage`, and `billing` output ports
- DMM should not show duplicated Bronze SourceSystem nodes for A1, and the A1 silver product should not list product-to-product consumes as ODPS input ports

## A2 Internal Reference

```bash
cd "$GREENFIELD_WORKSPACE/variants/A2-internal-reference"
set -a
source "$FLUID_SECRETS_FILE"
set +a
"$FLUID_CLI" validate contract.fluid.yaml
"$FLUID_CLI" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
"$FLUID_CLI" apply contract.fluid.yaml --mode amend-and-build --build dv2_subscriber360_internal_build --yes --report runtime/apply_report.html
"$FLUID_CLI" generate ci contract.fluid.yaml --system jenkins --install-mode "$JENKINS_INSTALL_MODE" --default-publish-target datamesh-manager --out Jenkinsfile
git status --short -- Jenkinsfile
git add Jenkinsfile
if ! git diff --cached --quiet -- Jenkinsfile; then
  git commit -m "Refresh internal-reference silver variant"
else
  echo "Jenkinsfile already committed"
fi
cd "$LAB_REPO"
task jenkins:sync SCENARIO=A2
task jenkins:build SCENARIO=A2
cd "$GREENFIELD_WORKSPACE/variants/A2-internal-reference"
rm -rf "$LAB_REPO/airflow/dags/active/current"
"$FLUID_CLI" schedule-sync --scheduler airflow --dags-dir airflow_subscriber360/dags --destination "$LAB_REPO/airflow/dags/active/current"
"$FLUID_CLI" publish contract.fluid.yaml --target datamesh-manager
```

Validation:

- Jenkins now lists `A2-internal-reference`; it did not exist before `task jenkins:sync`
- `task jenkins:build SCENARIO=A2` runs the controller build through Jenkins `buildWithParameters` and confirms the pipeline reads `variants/A2-internal-reference/Jenkinsfile`
- in the demo-release track, `task jenkins:sync` and `task jenkins:build` automatically carry the package resolved in `runtime/generated/demo-release.env`; do not add manual TestPyPI `--param` flags unless you are deliberately overriding the launchpad
- the A2 Jenkins build should fail at stage `9 · verify` on `fluid verify ... --strict`; that failure is intentional in this lab and demonstrates the strict Snowflake contract gate on required vs nullable columns
- Airflow now lists DAG `telco_subscriber360_internal`; it did not exist before the `schedule-sync` command
- run `cd "$LAB_REPO" && task dbt:docs:refresh SCENARIO=A2`, then confirm dbt docs shows `mart_subscriber360_core` and `mart_subscriber_health_scorecard`
- DMM shows the A2 silver product with `subscriber360_core` and `subscriber_health_scorecard`; that comes from the explicit local `fluid publish` command above, not from the intentionally failing Jenkins build
- DMM Access agreements show A2 consuming the Bronze `party`, `usage`, and `billing` output ports; A2 should not create duplicate Bronze SourceSystem nodes or product-to-product ODPS input ports

## B1 AI External Reference

B1 starts with a live provider-backed AI forge. The lab command stores the raw AI output and receipt under `runtime/generated/ai-forge/`, then hardens the generated contract with the stable B1 build id, Bronze lineage anchors, and external dbt reference needed for the runnable Snowflake flow.

```bash
cd "$LAB_REPO"
task b1:forge:ai FLUID_BIN="$FLUID_CLI" -- --provider gemini --model gemini-2.5-flash
# OpenAI equivalent when OPENAI_API_KEY is available:
# task b1:forge:ai FLUID_BIN="$FLUID_CLI" -- --provider openai --model gpt-4.1-mini

cd "$EXISTING_DBT_WORKSPACE/variants/B1-ai-reference-external/subscriber360-external"
set -a
source "$FLUID_SECRETS_FILE"
set +a
export FLUID_UPSTREAM_CONTRACTS="$LAB_REPO/fluid/contracts"
export PATH="$(dirname "$FLUID_CLI"):$PATH"
unset DBT_TARGET
"$FLUID_CLI" validate contract.fluid.yaml
"$FLUID_CLI" generate transformation contract.fluid.yaml -o runtime/generated/dbt-preview --overwrite --dbt-validate
"$FLUID_CLI" generate schedule contract.fluid.yaml --scheduler airflow -o runtime/generated/airflow --overwrite
"$FLUID_CLI" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
"$FLUID_CLI" apply contract.fluid.yaml --mode amend-and-build --build ai_subscriber360_external_build --yes --report runtime/apply_report.html
"$FLUID_CLI" generate ci contract.fluid.yaml --system jenkins --install-mode "$JENKINS_INSTALL_MODE" --default-publish-target datamesh-manager --no-verify-strict-default --publish-stage-default --no-publish-include-env --out Jenkinsfile
git status --short -- contract.fluid.yaml Jenkinsfile
git add contract.fluid.yaml Jenkinsfile
if ! git diff --cached --quiet -- contract.fluid.yaml Jenkinsfile; then
  git commit -m "Refresh B1 AI external-reference variant"
else
  echo "B1 Jenkinsfile already committed"
fi
cd "$LAB_REPO"
task jenkins:sync SCENARIO=B1
task jenkins:build SCENARIO=B1
cd "$EXISTING_DBT_WORKSPACE/variants/B1-ai-reference-external/subscriber360-external"
rm -rf "$LAB_REPO/airflow/dags/active/current"
"$FLUID_CLI" schedule-sync --scheduler airflow --dags-dir runtime/generated/airflow --destination "$LAB_REPO/airflow/dags/active/current"
"$FLUID_CLI" publish contract.fluid.yaml --target datamesh-manager
```

Validation:

- `runtime/generated/ai-forge/summary.json` names the live AI provider/model used for the B1 contract
- the raw AI contract and receipt are preserved under `runtime/generated/ai-forge/raw/`
- Jenkins now lists `B1-ai-reference-external`; it did not exist before `task jenkins:sync`
- `task jenkins:build SCENARIO=B1` runs the Path B Pipeline-from-SCM job from `path-b-ai-telco-silver-import-demo`
- B1 uses the same non-strict verify and publish defaults as A1 so the Snowflake nullable-vs-required mismatch stays informational
- Airflow now lists DAG `silver_telco_subscriber360_ai_external_v1` from the generated schedule assets
- run `cd "$LAB_REPO" && task dbt:docs:refresh SCENARIO=B1`, then confirm dbt docs shows `mart_subscriber360_core` and `mart_subscriber_health_scorecard`
- DMM shows the B1 silver product with `subscriber360_core` and `subscriber_health_scorecard`
- DMM Access agreements show B1 consuming the Bronze `party`, `usage`, and `billing` output ports

## B2 MCP Generated Assets

B2 starts with the forge-cli MCP server reading the seeded Snowflake schema. The lab command stores the raw MCP model under `runtime/generated/mcp-forge/`, writes the deterministic B2 contract, and generates dbt, Airflow, and Jenkins assets inside the product workspace.

```bash
cd "$LAB_REPO"
task b2:forge:mcp FLUID_BIN="$FLUID_CLI"

cd "$EXISTING_DBT_WORKSPACE/variants/B2-ai-generate-in-workspace/subscriber360-generated"
set -a
source "$FLUID_SECRETS_FILE"
set +a
export FLUID_UPSTREAM_CONTRACTS="$LAB_REPO/fluid/contracts"
export PATH="$(dirname "$FLUID_CLI"):$PATH"
unset DBT_TARGET
"$FLUID_CLI" validate contract.fluid.yaml
"$FLUID_CLI" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
"$FLUID_CLI" apply contract.fluid.yaml --mode amend-and-build --build ai_subscriber360_generated_build --yes --report runtime/apply_report.html
git status --short -- contract.fluid.yaml Jenkinsfile generated
git add contract.fluid.yaml Jenkinsfile generated
if ! git diff --cached --quiet -- contract.fluid.yaml Jenkinsfile generated; then
  git commit -m "Refresh B2 MCP generated-assets variant"
else
  echo "B2 generated assets already committed"
fi
cd "$LAB_REPO"
task jenkins:sync SCENARIO=B2
task jenkins:build SCENARIO=B2
cd "$EXISTING_DBT_WORKSPACE/variants/B2-ai-generate-in-workspace/subscriber360-generated"
rm -rf "$LAB_REPO/airflow/dags/active/current"
"$FLUID_CLI" schedule-sync --scheduler airflow --dags-dir generated/airflow --destination "$LAB_REPO/airflow/dags/active/current"
"$FLUID_CLI" publish contract.fluid.yaml --target datamesh-manager
```

Validation:

- `runtime/generated/mcp-forge/summary.json` names the MCP server, Snowflake schema, and table count used for B2
- the raw MCP contract and logical model are preserved under `runtime/generated/mcp-forge/raw/`
- generated dbt assets live under `generated/dbt/dbt_dv2_subscriber360`
- generated Airflow assets live under `generated/airflow`
- Jenkins now lists `B2-ai-generate-in-workspace`; it did not exist before `task jenkins:sync`
- `task jenkins:build SCENARIO=B2` runs the Path B Pipeline-from-SCM job from `path-b-ai-telco-silver-import-demo`
- Airflow now lists DAG `silver_telco_subscriber360_ai_generated_v1` from the generated schedule assets
- run `cd "$LAB_REPO" && task dbt:docs:refresh SCENARIO=B2`, then confirm dbt docs shows `subscriber360_core` and `subscriber_health_scorecard`
- DMM shows the B2 silver product with `subscriber360_core` and `subscriber_health_scorecard`
- DMM Access agreements show B2 consuming the Bronze `party`, `usage`, and `billing` output ports

## Supporting Docs

- [Scenario Validation Matrix](scenario-validation-matrix.md)
- [Jenkins SCM Handoff](jenkins-scm-handoff.md)
- [Launchpad Recovery](launchpad-recovery.md)
