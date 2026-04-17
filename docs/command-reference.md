# Command Reference

These are the commands this repo promotes for the full local-Mac demo.

## Common Shell Variables

```bash
export LAB_REPO="/Users/A200004702/Documents/Open-Source Community/snowflake-biz-lab"
export GREENFIELD_WORKSPACE="$HOME/gitlab/telco-silver-product-demo"
export EXISTING_DBT_WORKSPACE="$HOME/gitlab/telco-silver-import-demo"
export FLUID_SECRETS_FILE="$LAB_REPO/runtime/generated/fluid.local.env"
```

## Local Platform Control

```bash
cd "$LAB_REPO"
task up
task jenkins:up
task catalogs:up
task ps
task logs
task catalogs:logs
```

## Seed And Metadata Flow

```bash
cd "$LAB_REPO"
task seed:generate
task seed:load
task seed:verify
task metadata:apply
task metadata:verify
```

## Install The Released CLI In A Demo Workspace

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ data-product-forge==0.7.10
fluid version
fluid doctor
```

## Load Runtime Secrets Before Live Commands

```bash
set -a
source "$FLUID_SECRETS_FILE"
set +a
```

## Greenfield Workspace Flow

```bash
cd "$GREENFIELD_WORKSPACE"
fluid init telco-silver-product --provider snowflake --yes
cd telco-silver-product
fluid forge --provider snowflake --domain telco --target-dir .
fluid generate schedule contract.fluid.yaml --scheduler airflow -o generated/airflow --overwrite
fluid generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
fluid validate contract.fluid.yaml
fluid plan contract.fluid.yaml --out runtime/plan.json --html
fluid apply contract.fluid.yaml --yes --report runtime/apply_report.html
fluid generate standard contract.fluid.yaml --format opds -o runtime/exports/product.opds.json
fluid generate standard contract.fluid.yaml --format odcs -o runtime/exports/product.odcs.yaml
fluid generate standard contract.fluid.yaml --format odps -o runtime/exports/product.odps.yaml
fluid dmm publish contract.fluid.yaml --with-contract --validate-generated-contracts
```

## Existing dbt Variation

```bash
cd "$EXISTING_DBT_WORKSPACE"
rsync -a "$LAB_REPO/dbt/" ./dbt/
mkdir -p config
rsync -a "$LAB_REPO/config/dbt/" ./config/dbt/
fluid import --dir ./dbt --provider snowflake --yes
fluid forge --provider snowflake --domain telco --target-dir . --discovery-path ./dbt
fluid generate schedule contract.fluid.yaml --scheduler airflow -o generated/airflow --overwrite
fluid generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
fluid validate contract.fluid.yaml
fluid plan contract.fluid.yaml --out runtime/plan.json --html
```

## Repo Runtime Checks

```bash
cd "$LAB_REPO"
task fluid:bootstrap:demo
task fluid:check:demo
task fluid:bootstrap:dev
task fluid:check:dev
```

## Repo Contract Shortcuts

```bash
cd "$LAB_REPO"
.venv.fluid-demo/bin/fluid validate fluid/contracts/snowflake_smoke/contract.fluid.yaml
.venv.fluid-demo/bin/fluid validate fluid/contracts/telco_stage_seed/contract.fluid.yaml
```

If you hit a mismatch between the target end-state commands and the current release behavior, capture it in the [FLUID Gap Register](fluid-gap-register.md).
