# Mac Greenfield Demo

This is the primary target end-state demo.

It starts with local apps on your Mac, seeds Snowflake staging, creates a GitLab-based FLUID workspace, and ends with standards export plus local DMM publish.

## Standard Shell Variables

```bash
export LAB_REPO="/Users/A200004702/Documents/Open-Source Community/snowflake-biz-lab"
export GREENFIELD_WORKSPACE="$LAB_REPO/gitlab/path-a-telco-silver-product-demo"
export FLUID_SECRETS_FILE="$LAB_REPO/runtime/generated/fluid.local.env"
```

The `./gitlab/` directory inside the lab repo is gitignored and bootstrapped from `fluid/fixtures/workspaces/` via `task workspaces:bootstrap`.

## Step 1: Bring Up The Local Platform

```bash
cd "$LAB_REPO"
task up
task jenkins:up
task catalogs:up
task catalogs:bootstrap
task ps
```

Checkpoint:

- Airflow opens at [http://localhost:8085](http://localhost:8085)
- dbt docs opens at [http://localhost:8086](http://localhost:8086)
- Jenkins opens at [http://localhost:8081](http://localhost:8081)
- Entropy / DMM opens at [http://localhost:8095](http://localhost:8095)
- the Entropy admin account is already usable
- `DMM_API_KEY` has been refreshed in `runtime/generated/fluid.local.env`

## Step 2: Reset Demo State And Seed Snowflake Staging

This step starts by wiping the demo database and re-bootstrapping the GitLab workspaces from tracked templates, so only point it at disposable demo Snowflake objects.

```bash
cd "$LAB_REPO"
task workspaces:reset
task seed:reset:confirm
task seed:generate
task seed:load
task seed:verify
task metadata:apply
task metadata:verify
```

Checkpoint:

- `./gitlab/path-a-telco-silver-product-demo/` shows the A1 contract and the A2 internal assets, with no `Jenkinsfile` yet
- `./gitlab/path-b-ai-telco-silver-import-demo/` is empty (B1/B2 forge the contract live)
- the telco landing tables exist in `SNOWFLAKE_STAGE_SCHEMA`
- Horizon metadata is applied on those source tables before FLUID starts building the silver story
- table and column descriptions are visible in Horizon without needing dbt-built schemas first

## Step 3: Install `data-product-forge` In The GitLab Workspace

```bash
cd "$GREENFIELD_WORKSPACE"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
# Pulls the LATEST data-product-forge from TestPyPI by design (release candidates
# ship there before stable PyPI). PyPI is only a fallback for transitive deps.
# To pin: `pip install data-product-forge==X.Y.Z` with the same flags.
# To use stable PyPI instead: drop `--index-url`.
pip install --pre --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ data-product-forge
fluid version
fluid doctor
```

Checkpoint:

- you have shown the install step live
- the room sees the released CLI, not a hidden local checkout

## Step 4: Start The FLUID Workspace

```bash
cd "$GREENFIELD_WORKSPACE"
fluid init telco-silver-product --provider snowflake --yes
cd telco-silver-product
```

Checkpoint:

- you are now working in the GitLab path on your Mac
- the demo has moved from platform prep into data-product authoring

## Step 5: Load Runtime Secrets

```bash
set -a
source "$FLUID_SECRETS_FILE"
set +a
```

Checkpoint:

- you can say clearly that secrets live outside the contract

## Step 6: Forge The Silver-Layer Data Product

Run:

```bash
fluid forge --provider snowflake --domain telco --target-dir .
```

Suggested spoken prompt for the AI step:

See [Greenfield Forge Prompt](greenfield-forge-prompt.md).

Checkpoint:

- the story is now clearly about a silver aggregated telco product
- you have shown AI-assisted contract authoring, not just a static file

## Step 7: Generate Airflow And Jenkins

```bash
fluid generate schedule contract.fluid.yaml --scheduler airflow -o generated/airflow --overwrite
fluid generate ci contract.fluid.yaml --system jenkins --default-publish-target datamesh-manager --out Jenkinsfile
```

Checkpoint:

- local Airflow can now watch the generated DAG directory through the workspace bridge
- run `task dbt:docs:refresh SCENARIO=B2` from `$LAB_REPO` when you want the generated dbt project visible at [http://localhost:8086](http://localhost:8086)
- a `Jenkinsfile` exists in the workspace for the CI/CD part of the story

## Step 8: Validate And Plan

```bash
fluid validate contract.fluid.yaml
fluid plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
```

Checkpoint:

- the plan JSON is saved in `runtime/plan.json`
- the HTML view is saved in `runtime/plan.html`
- review [Plan Verification Checklist](../../docs/plan-verification-checklist.md) before you continue
- this is the best moment to narrate what FLUID will do before you apply it

## Step 9: Apply

```bash
BUILD_ID="$(python3 "$LAB_REPO/scripts/get_first_build_id.py" contract.fluid.yaml)"
fluid apply contract.fluid.yaml --build "$BUILD_ID" --yes --report runtime/apply_report.html
```

Checkpoint:

- the data product deployment step has run
- the apply report is saved in `runtime/apply_report.html`

The generated Jenkins handoff now follows [Jenkins SCM Handoff](../../docs/jenkins-scm-handoff.md).

## Step 10: Export Standards And Publish To DMM

```bash
fluid generate standard contract.fluid.yaml --format opds -o runtime/exports/product.opds.json
fluid generate standard contract.fluid.yaml --format odcs -o runtime/exports/product.odcs.yaml
fluid generate standard contract.fluid.yaml --format odps -o runtime/exports/product.odps.yaml
fluid publish contract.fluid.yaml --catalog datamesh-manager
```

Checkpoint:

- you end with standards artifacts plus marketplace publication
- Entropy / DMM becomes the closing product-discovery story

## Presenter Notes

- Say out loud that the demo uses the released CLI from TestPyPI.
- Say out loud that `fluidVersion` inside the contract is a separate compatibility layer.
- Keep the [FLUID Gap Register](../../docs/fluid-gap-register.md) open so you can note any release gaps you want to fix later in `forge-cli`.
