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

- **A1** external-reference silver contract
- **A2** internal-reference silver contract
- **B1** AI forge with external references
- **B2** AI forge with generated assets

Use [Scenario Validation Matrix](scenario-validation-matrix.md) for the exact contract paths, dbt roots, DAG paths, DAG IDs, Jenkinsfile paths, and expose names.

## Workspace A: Ready-Made Variants

### A1 External Reference

```bash
cd "$GREENFIELD_WORKSPACE/variants/external-reference"
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
- open Jenkins at [http://localhost:8081](http://localhost:8081) and confirm SCM pickup for `variants/external-reference/Jenkinsfile`

### A2 Internal Reference

```bash
cd "$GREENFIELD_WORKSPACE/variants/internal-reference"
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
- open Jenkins at [http://localhost:8081](http://localhost:8081) and confirm SCM pickup for `variants/internal-reference/Jenkinsfile`

## Workspace B: AI Variants

The AI-created workspaces are expected to land here:

```text
$EXISTING_DBT_WORKSPACE/variants/ai-reference-external/subscriber360-external
$EXISTING_DBT_WORKSPACE/variants/ai-generate-in-workspace/subscriber360-generated
```

### B1 AI Forge + External References

```bash
cd "$EXISTING_DBT_WORKSPACE/variants/ai-reference-external"
source "$EXISTING_DBT_WORKSPACE/.venv/bin/activate"
set -a
source "$FLUID_SECRETS_FILE"
set +a
cat ../../prompts/ai-reference-external.md
fluid init subscriber360-external --provider snowflake --yes
cd subscriber360-external
fluid forge --provider snowflake --domain telco --target-dir .
fluid validate contract.fluid.yaml
fluid plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
BUILD_ID="$(python3 - <<'PY'
from pathlib import Path
in_builds = False
for raw in Path('contract.fluid.yaml').read_text().splitlines():
    stripped = raw.strip()
    if stripped == 'builds:':
        in_builds = True
        continue
    if in_builds and (stripped.startswith('- id:') or stripped.startswith('id:')):
        print(stripped.split(':', 1)[1].strip())
        break
PY
)"
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
- open Jenkins at [http://localhost:8081](http://localhost:8081) and confirm SCM pickup for `variants/ai-reference-external/subscriber360-external/Jenkinsfile`

### B2 AI Forge + Generated Assets

```bash
cd "$EXISTING_DBT_WORKSPACE/variants/ai-generate-in-workspace"
source "$EXISTING_DBT_WORKSPACE/.venv/bin/activate"
set -a
source "$FLUID_SECRETS_FILE"
set +a
cat ../../prompts/ai-generate-in-workspace.md
fluid init subscriber360-generated --provider snowflake --yes
cd subscriber360-generated
fluid forge --provider snowflake --domain telco --target-dir .
fluid validate contract.fluid.yaml
fluid plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
fluid generate transformation contract.fluid.yaml --engine dbt -o generated/dbt --overwrite
fluid generate schedule contract.fluid.yaml --scheduler airflow -o generated/airflow --overwrite
BUILD_ID="$(python3 - <<'PY'
from pathlib import Path
in_builds = False
for raw in Path('contract.fluid.yaml').read_text().splitlines():
    stripped = raw.strip()
    if stripped == 'builds:':
        in_builds = True
        continue
    if in_builds and (stripped.startswith('- id:') or stripped.startswith('id:')):
        print(stripped.split(':', 1)[1].strip())
        break
PY
)"
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
- open Jenkins at [http://localhost:8081](http://localhost:8081) and confirm SCM pickup for `variants/ai-generate-in-workspace/subscriber360-generated/Jenkinsfile`

## Jenkins SCM Handoff

After each `fluid generate ci` step:

1. commit the generated `Jenkinsfile`
2. push the workspace repo to GitLab
3. let Jenkins pick up the pipeline from SCM

Use [Jenkins SCM Handoff](jenkins-scm-handoff.md) for the expected script paths and job model.

## Related Docs

- [Launchpad Common](launchpad-common.md)
- [Plan Verification Checklist](plan-verification-checklist.md)
- [Scenario Validation Matrix](scenario-validation-matrix.md)
- [Jenkins SCM Handoff](jenkins-scm-handoff.md)
- [Demo Release Launchpad (Windows)](demo-release-launchpad-windows.md)
- Workspace A root: `gitlab/telco-silver-product-demo`
- Workspace B root: `gitlab/telco-silver-import-demo`
