# Variant Playbook (Mac)

Shared Bronze, A1, and A2 commands for macOS. Your chosen track launchpad must already have exported `FLUID_CLI`, `FLUID_SECRETS_FILE`, and `JENKINS_INSTALL_MODE`.

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

## Supporting Docs

- [Scenario Validation Matrix](scenario-validation-matrix.md)
- [Jenkins SCM Handoff](jenkins-scm-handoff.md)
- [Launchpad Recovery](launchpad-recovery.md)
