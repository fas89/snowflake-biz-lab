# Mac Existing dbt Demo

This is the secondary variation for teams that already have dbt assets and want FLUID to reference or enrich them.

## Standard Shell Variables

```bash
export LAB_REPO="/Users/A200004702/Documents/Open-Source Community/snowflake-biz-lab"
export EXISTING_DBT_WORKSPACE="$LAB_REPO/gitlab/path-b-ai-telco-silver-import-demo"
export FLUID_SECRETS_FILE="$LAB_REPO/runtime/generated/fluid.local.env"
```

## Before You Start

Make sure the demo workspaces are freshly bootstrapped so the import demo starts from an empty `path-b-ai-telco-silver-import-demo`:

```bash
cd "$LAB_REPO"
task workspaces:reset
```

Use `task workspaces:bootstrap` instead if the workspaces already exist and you want to keep whatever is there.

docker-compose mounts `./gitlab/path-a-telco-silver-product-demo` (greenfield) and `./gitlab/path-b-ai-telco-silver-import-demo` (AI/import) into Airflow by default, so no `.env` changes are needed for the standard layout.

## Step 1: Install `data-product-forge`

```bash
cd "$EXISTING_DBT_WORKSPACE"
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
fluid generate ci contract.fluid.yaml --system jenkins --default-publish-target datamesh-manager --out Jenkinsfile
```

## Step 7: Validate And Plan

```bash
fluid validate contract.fluid.yaml
fluid plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
```

## Step 8: Continue Into The Full Tail If The Room Has Time

```bash
BUILD_ID="$(python3 "$LAB_REPO/scripts/get_first_build_id.py" contract.fluid.yaml)"
fluid apply contract.fluid.yaml --build "$BUILD_ID" --yes --report runtime/apply_report.html
fluid generate standard contract.fluid.yaml --format opds -o runtime/exports/product.opds.json
fluid generate standard contract.fluid.yaml --format odcs -o runtime/exports/product.odcs.yaml
fluid generate standard contract.fluid.yaml --format odps -o runtime/exports/product.odps.yaml
fluid publish contract.fluid.yaml --catalog datamesh-manager
```

If the current release diverges from the target story here, capture it in the [FLUID Gap Register](../../docs/fluid-gap-register.md).
