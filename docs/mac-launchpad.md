# Mac Demo Launchpad

This is the top operator page for running the Snowflake telco demo from your Mac.

## Standard Local Paths

```bash
export LAB_REPO="/Users/A200004702/Documents/Open-Source Community/snowflake-biz-lab"
export GREENFIELD_WORKSPACE="$HOME/gitlab/telco-silver-product-demo"
export EXISTING_DBT_WORKSPACE="$HOME/gitlab/telco-silver-import-demo"
export FLUID_SECRETS_FILE="$LAB_REPO/runtime/generated/fluid.local.env"
```

## Browser Tabs To Open

- Airflow: [http://localhost:8085](http://localhost:8085)
- Jenkins: [http://localhost:8081](http://localhost:8081)
- Entropy / DMM: [http://localhost:8095](http://localhost:8095)
- MailHog: [http://localhost:8026](http://localhost:8026)

## Repo Docs To Keep Handy

- [Getting Started](getting-started.md)
- [Credentials](credentials.md)
- [Command Reference](command-reference.md)
- [Mac Greenfield Demo](../fluid/demo/mac-greenfield-demo.md)
- [Mac Existing dbt Demo](../fluid/demo/mac-existing-dbt-demo.md)
- [Rehearsal Checklist](../fluid/demo/rehearsal-checklist.md)
- [FLUID Gap Register](fluid-gap-register.md)

## External Links To Keep Handy

- TestPyPI package: [data-product-forge](https://test.pypi.org/project/data-product-forge/)
- Forge docs home: [Forge Docs](https://agenticstiger.github.io/forge_docs/)
- Snowflake quickstart: [Forge Snowflake Getting Started](https://agenticstiger.github.io/forge_docs/getting-started/snowflake)
- Source repo: [forge-cli](https://github.com/Agenticstiger/forge-cli)

## One-Time Local Setup

### 1. Copy The Local Env Files

```bash
cd "$LAB_REPO"
cp .env.example .env
cp .env.catalogs.example .env.catalogs
cp .env.jenkins.example .env.jenkins
```

### 2. Set The Active GitLab Workspace For Airflow

In `.env`, set:

```text
FLUID_DEMO_GITLAB_WORKSPACE=/Users/A200004702/gitlab/telco-silver-product-demo
```

Use an absolute path, not `~`.

Airflow will mount:

```text
${FLUID_DEMO_GITLAB_WORKSPACE}/generated/airflow
```

into its DAG directory.

### 3. Prepare Local Secret Material

Create or update:

```text
$LAB_REPO/runtime/generated/fluid.local.env
```

This file holds live Snowflake and DMM credentials only.

### 4. Prepare The GitLab Working Copies

```bash
mkdir -p "$HOME/gitlab"
git clone <your-greenfield-gitlab-url> "$GREENFIELD_WORKSPACE"
git clone <your-existing-dbt-gitlab-url> "$EXISTING_DBT_WORKSPACE"
```

## Off-Stage Prep Commands

### Start The Local Apps

```bash
cd "$LAB_REPO"
task up
task jenkins:up
task catalogs:up
task ps
```

### Seed Snowflake Staging And Apply Metadata

```bash
cd "$LAB_REPO"
task seed:generate
task seed:load
task seed:verify
task metadata:apply
task metadata:verify
```

### Verify The Browser Tabs

- Airflow: [http://localhost:8085](http://localhost:8085)
- Jenkins: [http://localhost:8081](http://localhost:8081)
- Entropy / DMM: [http://localhost:8095](http://localhost:8095)
- MailHog: [http://localhost:8026](http://localhost:8026)

## Live Greenfield Command Sequence

```bash
cd "$GREENFIELD_WORKSPACE"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ data-product-forge==0.7.10
fluid version
fluid init telco-silver-product --provider snowflake --yes
cd telco-silver-product
set -a
source "$FLUID_SECRETS_FILE"
set +a
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

Full notes: [Mac Greenfield Demo](../fluid/demo/mac-greenfield-demo.md)

## Live Existing dbt Command Sequence

```bash
cd "$EXISTING_DBT_WORKSPACE"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ data-product-forge==0.7.10
fluid version
rsync -a "$LAB_REPO/dbt/" ./dbt/
mkdir -p config
rsync -a "$LAB_REPO/config/dbt/" ./config/dbt/
set -a
source "$FLUID_SECRETS_FILE"
set +a
fluid import --dir ./dbt --provider snowflake --yes
fluid forge --provider snowflake --domain telco --target-dir . --discovery-path ./dbt
fluid generate schedule contract.fluid.yaml --scheduler airflow -o generated/airflow --overwrite
fluid generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
fluid validate contract.fluid.yaml
fluid plan contract.fluid.yaml --out runtime/plan.json --html
```

Full notes: [Mac Existing dbt Demo](../fluid/demo/mac-existing-dbt-demo.md)

## Switching Airflow To The Existing dbt Workspace

If you want the local Airflow UI to show the generated DAGs from the secondary demo instead of the greenfield demo:

1. change `FLUID_DEMO_GITLAB_WORKSPACE` in `.env`
2. restart the core stack

```bash
cd "$LAB_REPO"
task down
task up
```

## Final Demo Support Docs

- [Rehearsal Checklist](../fluid/demo/rehearsal-checklist.md)
- [FLUID Gap Register](fluid-gap-register.md)
- [Backup Demo](../fluid/demo/backup-demo.md)
