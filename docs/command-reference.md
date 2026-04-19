# Command Reference

These are the commands this repo promotes for the full local demo.

## Common Shell Variables

```bash
export LOCAL_REPOS_DIR="/absolute/path/to/your/local/repos"
export LAB_REPO="$LOCAL_REPOS_DIR/snowflake-biz-lab"
export GREENFIELD_WORKSPACE="$LOCAL_REPOS_DIR/gitlab/telco-silver-product-demo"
export EXISTING_DBT_WORKSPACE="$LOCAL_REPOS_DIR/gitlab/telco-silver-import-demo"
export FLUID_SECRETS_FILE="$LAB_REPO/runtime/generated/fluid.local.env"
```

## Local Platform Control

```bash
cd "$LAB_REPO"
task up
task jenkins:up
task catalogs:up
task catalogs:bootstrap
task ps
task logs
task catalogs:logs
task catalogs:reset
```

## Seed And Metadata Flow

`task seed:reset` is destructive. It drops the entire database in `SNOWFLAKE_DATABASE`.

```bash
cd "$LAB_REPO"
task seed:reset
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
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ data-product-forge
fluid version
fluid doctor
```

## Load Runtime Secrets Before Live Commands

```bash
set -a
source "$FLUID_SECRETS_FILE"
set +a
```

## Ready-Made Workspace Flow

```bash
cd "$GREENFIELD_WORKSPACE"
source .venv/bin/activate
cd variants/external-reference
fluid validate contract.fluid.yaml
fluid plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
fluid apply contract.fluid.yaml --build --yes --report runtime/apply_report.html
fluid generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Refresh external-reference silver variant"
git push
fluid publish contract.fluid.yaml --catalog entropy-local
```

Review the plan before apply with [Plan Verification Checklist](plan-verification-checklist.md).

## AI Workspace Flow

```bash
cd "$EXISTING_DBT_WORKSPACE"
source .venv/bin/activate
cd variants/ai-reference-external
cat ../../prompts/ai-reference-external.md
fluid init subscriber360-external --provider snowflake --yes
cd subscriber360-external
fluid forge --provider snowflake --domain telco --target-dir .
fluid validate contract.fluid.yaml
fluid plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
fluid apply contract.fluid.yaml --build --yes --report runtime/apply_report.html
fluid generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Generate AI external-reference silver variant"
git push
fluid publish contract.fluid.yaml --catalog entropy-local
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
.venv.fluid-demo/bin/fluid validate fluid/contracts/telco_seed_sources/contract.fluid.yaml
.venv.fluid-demo/bin/fluid validate fluid/contracts/telco_stage_seed/contract.fluid.yaml
```

If you hit a mismatch between the target end-state commands and the current release behavior, capture it in the [FLUID Gap Register](fluid-gap-register.md).
