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
| Bronze | Upstream lineage anchor | `$LAB_REPO` | `fluid/contracts/telco_seed_sources/contract.fluid.yaml` | No dbt/Airflow/Jenkins assets | schema, parser, publish, lineage anchor |
| A1 | External-reference silver contract | `$GREENFIELD_WORKSPACE` | `variants/external-reference/contract.fluid.yaml` | referenced dbt + referenced Airflow | reference resolution, plan/apply, publish |
| A2 | Internal-reference silver contract | `$GREENFIELD_WORKSPACE` | `variants/internal-reference/contract.fluid.yaml` | packaged dbt + packaged Airflow | packaging, plan/apply, publish |
| B1 | AI forge with external references | `$EXISTING_DBT_WORKSPACE` | `variants/ai-reference-external/subscriber360-external` | referenced dbt + referenced Airflow | forge interview, reference resolution |
| B2 | AI forge with generated assets | `$EXISTING_DBT_WORKSPACE` | `variants/ai-generate-in-workspace/subscriber360-generated` | generated dbt + generated Airflow | generation, transformation generation, schedule generation |

Use [Scenario Validation Matrix](scenario-validation-matrix.md) for the exact contract paths, dbt roots, DAG paths, DAG IDs, Jenkinsfile paths, and expose names.

## Bronze Anchor Scenario

```bash
cd "$LAB_REPO"
set -a
source "$FLUID_SECRETS_FILE"
set +a
"$FLUID_DEV_BIN" validate fluid/contracts/telco_seed_sources/contract.fluid.yaml
"$FLUID_DEV_BIN" plan fluid/contracts/telco_seed_sources/contract.fluid.yaml --out fluid/contracts/telco_seed_sources/runtime/plan.json --html
open fluid/contracts/telco_seed_sources/runtime/plan.html
"$FLUID_DEV_BIN" publish fluid/contracts/telco_seed_sources/contract.fluid.yaml --catalog datamesh-manager
```

Validation:

- review the bronze plan against [Plan Verification Checklist](plan-verification-checklist.md)
- confirm the bronze contract publishes as the lineage anchor
- no Airflow, dbt, or Jenkins assets are expected for this scenario

## Workspace A: Ready-Made Variants

### A1 External Reference

```bash
cd "$GREENFIELD_WORKSPACE/variants/external-reference"
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
- open Jenkins at [http://localhost:8081](http://localhost:8081) and confirm SCM pickup for `variants/external-reference/Jenkinsfile`

### A2 Internal Reference

```bash
cd "$GREENFIELD_WORKSPACE/variants/internal-reference"
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
set -a
source "$FLUID_SECRETS_FILE"
set +a
cat ../../prompts/ai-reference-external.md
"$FLUID_DEV_BIN" init subscriber360-external --provider snowflake --yes
cd subscriber360-external
"$FLUID_DEV_BIN" forge --provider snowflake --domain telco --target-dir .
"$FLUID_DEV_BIN" validate contract.fluid.yaml
"$FLUID_DEV_BIN" plan contract.fluid.yaml --out runtime/plan.json --html
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
- open Jenkins at [http://localhost:8081](http://localhost:8081) and confirm SCM pickup for `variants/ai-reference-external/subscriber360-external/Jenkinsfile`

### B2 AI Forge + Generated Assets

```bash
cd "$EXISTING_DBT_WORKSPACE/variants/ai-generate-in-workspace"
set -a
source "$FLUID_SECRETS_FILE"
set +a
cat ../../prompts/ai-generate-in-workspace.md
"$FLUID_DEV_BIN" init subscriber360-generated --provider snowflake --yes
cd subscriber360-generated
"$FLUID_DEV_BIN" forge --provider snowflake --domain telco --target-dir .
"$FLUID_DEV_BIN" validate contract.fluid.yaml
"$FLUID_DEV_BIN" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
"$FLUID_DEV_BIN" generate transformation contract.fluid.yaml --engine dbt -o generated/dbt --overwrite
"$FLUID_DEV_BIN" generate schedule contract.fluid.yaml --scheduler airflow -o generated/airflow --overwrite
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
- open Jenkins at [http://localhost:8081](http://localhost:8081) and confirm SCM pickup for `variants/ai-generate-in-workspace/subscriber360-generated/Jenkinsfile`

## Jenkins SCM Handoff

After each `generate ci` step:

1. commit the generated `Jenkinsfile`
2. push the workspace repo to GitLab
3. let Jenkins pick up the pipeline from SCM

Use [Jenkins SCM Handoff](jenkins-scm-handoff.md) for the expected script paths and job model.

## Related Docs

- [Launchpad Common](launchpad-common.md)
- [Plan Verification Checklist](plan-verification-checklist.md)
- [Scenario Validation Matrix](scenario-validation-matrix.md)
- [Jenkins SCM Handoff](jenkins-scm-handoff.md)
- [Dev Source Launchpad (Windows)](dev-source-launchpad-windows.md)
- Workspace A root: `gitlab/telco-silver-product-demo`
- Workspace B root: `gitlab/telco-silver-import-demo`
