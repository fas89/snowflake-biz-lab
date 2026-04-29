# Troubleshooting

## Airflow Does Not Show The Generated DAGs

Confirm the active Airflow destination is where the playbook expects:

```bash
ls airflow/dags/active
```

Then rerun the native sync from the scenario directory:

```bash
"$FLUID_CLI" schedule-sync --scheduler airflow --dags-dir ../../reference-assets/airflow_subscriber360/dags --destination "$LAB_REPO/airflow/dags/active/current"
```

If the UI still looks stale, recycle the core stack:

```bash
task down
task up
```

## `fluid: command not found`

Use the venv binary directly:

```bash
.venv.fluid-demo/bin/fluid version
```

If the venv does not exist yet:

```bash
task fluid:bootstrap:demo
```

Or install the release directly in your GitLab workspace:

```bash
LATEST_TESTPYPI_VERSION="$(
  python -m pip index versions --pre --index-url https://test.pypi.org/simple/ data-product-forge \
    | sed -n 's/^data-product-forge (\([^)]*\)).*/\1/p' \
    | head -n1
)"
pip install --index-url https://pypi.org/simple/ --extra-index-url https://test.pypi.org/simple/ "data-product-forge[snowflake]==${LATEST_TESTPYPI_VERSION}"
```

## TestPyPI Install Feels Flaky

Use the same install shape the repo expects:

```bash
LATEST_TESTPYPI_VERSION="$(
  python -m pip index versions --pre --index-url https://test.pypi.org/simple/ data-product-forge \
    | sed -n 's/^data-product-forge (\([^)]*\)).*/\1/p' \
    | head -n1
)"
pip install --index-url https://pypi.org/simple/ --extra-index-url https://test.pypi.org/simple/ "data-product-forge[snowflake]==${LATEST_TESTPYPI_VERSION}"
```

If the venue network is unreliable, use the backup wheel path described in [fluid/demo/backup-demo.md](../fluid/demo/backup-demo.md).

## `task fluid:check:dev` Fails

That usually means the sibling `../forge-cli` checkout is not aligned with remote `main`.

Try:

```bash
git -C ../forge-cli checkout main
git -C ../forge-cli pull --ff-only origin main
task fluid:check:dev
```

## I Installed The Latest TestPyPI Release, But The Contract Still Says `0.7.2`

That is expected in this repo. Read [CLI Version vs `fluidVersion`](fluid-versions.md).

## Older CLI Builds Mention `llm_models.json`

You may see a warning like this during `validate` or `plan`:

```text
Could not load model catalog ... llm_models.json
```

Older TestPyPI `data-product-forge` builds could print that warning even when the contract workflow still succeeded. The current local `forge-cli` source includes the model catalog as package data, so this should not appear when you run against the dev checkout.

If `validate`, `plan`, or `doctor` finishes successfully, you can continue with the demo. Treat it as a release quirk, not as an automatic stop signal.

## Jenkins Publish Fails With DMM `403`

Jenkins reads `runtime/generated/fluid.local.env` when the container starts.

If you refreshed the local catalog with `task catalogs:bootstrap` after Jenkins was already running, reload Jenkins so it picks up the fresh `DMM_API_KEY`:

```bash
task catalogs:bootstrap
task jenkins:up
```

In this lab, Jenkins reaches the local catalog through `http://host.docker.internal:8095`, not `http://localhost:8095`.

## `fluid apply` Fails On Snowflake Authentication

Check the env file first:

```bash
set -a
source runtime/generated/fluid.local.env
set +a
```

Then confirm the basics:

- correct `SNOWFLAKE_ACCOUNT`
- correct `SNOWFLAKE_USER`
- working `SNOWFLAKE_ROLE`
- reachable warehouse, database, and schema
- key-pair or OAuth values loaded when you are not using password auth

## `fluid publish` Fails

Check the publish configuration and runtime env first:

```bash
set -a
source runtime/generated/fluid.local.env
set +a
```

Then confirm:

- your local catalog alias points at the Entropy / DMM sandbox endpoint you intend to use
- `DMM_API_URL` points to your local Entropy stack, usually `http://localhost:8095`
- `DMM_API_KEY` is present if your publish target needs it
- the Entropy UI opens at [http://localhost:8095](http://localhost:8095)

If the key is missing or stale, rerun:

```bash
task catalogs:bootstrap
```

## Telco Contract Fails Because Stage Tables Are Missing

The telco FLUID contract expects seeded landing tables to already exist.

Prepare them before the live apply:

```bash
task up
task seed:reset:confirm
task seed:generate
task seed:load
```

## `fluid generate ci --system jenkins` Creates A File, But Nothing Runs Yet

That is expected until you hand the generated `Jenkinsfile` off through Git and SCM.

The current supported path is:

1. generate the `Jenkinsfile`
2. commit and push the workspace repo to GitLab
3. let Jenkins discover the pipeline from SCM

See [Jenkins SCM Handoff](jenkins-scm-handoff.md).

## dbt Docs UI Is Empty Or Showing The Wrong Scenario

Refresh the docs site for the scenario you just ran:

```bash
task dbt:docs:refresh SCENARIO=A1
```

Then reopen [http://localhost:8086](http://localhost:8086).

See [Scenario Validation Matrix](scenario-validation-matrix.md) for the valid scenario names and expected dbt roots.

## I Want The Shortest Demo Rescue Path

Use [Backup Demo](../fluid/demo/backup-demo.md). It keeps the story small and dependency-light.
