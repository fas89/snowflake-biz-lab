# Mac Existing dbt Demo

This is the secondary variation for teams that already have dbt assets and want FLUID to reference or enrich them.

## Standard Shell Variables

```bash
export LAB_REPO="/Users/A200004702/Documents/Open-Source Community/snowflake-biz-lab"
export EXISTING_DBT_WORKSPACE="$LOCAL_REPOS_DIR/gitlab/telco-silver-import-demo"
export FLUID_SECRETS_FILE="$LAB_REPO/runtime/generated/fluid.local.env"
```

## Before You Start

If you want local Airflow to show the generated DAGs from this workspace, change `FLUID_DEMO_GITLAB_WORKSPACE` in `$LAB_REPO/.env` to this workspace and restart the core stack:

```bash
cd "$LAB_REPO"
task down
task up
```

## Step 1: Install `data-product-forge`

```bash
cd "$EXISTING_DBT_WORKSPACE"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ data-product-forge
fluid version
fluid doctor
```

## Step 2: Bring The Existing dbt Project Into The Workspace

```bash
cd "$EXISTING_DBT_WORKSPACE"
rsync -a "$LAB_REPO/dbt/" ./dbt/
mkdir -p config
rsync -a "$LAB_REPO/config/dbt/" ./config/dbt/
```

Checkpoint:

- the workspace now has an existing dbt project to reference

## Step 3: Load Runtime Secrets

```bash
set -a
source "$FLUID_SECRETS_FILE"
set +a
```

## Step 4: Import The Existing dbt Project

```bash
fluid import --dir ./dbt --provider snowflake --yes
```

Checkpoint:

- FLUID has scanned the existing dbt project and generated the starting contract shape

## Step 5: Optionally Enrich The Imported Contract With AI

```bash
fluid forge --provider snowflake --domain telco --target-dir . --discovery-path ./dbt
```

Suggested spoken prompt:

See [Existing dbt Forge Prompt](existing-dbt-forge-prompt.md).

## Step 6: Generate Airflow And Jenkins

```bash
fluid generate schedule contract.fluid.yaml --scheduler airflow -o generated/airflow --overwrite
fluid generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
```

## Step 7: Validate And Plan

```bash
fluid validate contract.fluid.yaml
fluid plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
```

## Step 8: Continue Into The Full Tail If The Room Has Time

```bash
fluid apply contract.fluid.yaml --build --yes --report runtime/apply_report.html
fluid generate standard contract.fluid.yaml --format opds -o runtime/exports/product.opds.json
fluid generate standard contract.fluid.yaml --format odcs -o runtime/exports/product.odcs.yaml
fluid generate standard contract.fluid.yaml --format odps -o runtime/exports/product.odps.yaml
fluid publish contract.fluid.yaml --catalog entropy-local
```

If the current release diverges from the target story here, capture it in the [FLUID Gap Register](../../docs/fluid-gap-register.md).
