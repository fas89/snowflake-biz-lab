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

## Pre-2 (Airbyte) Build Fails With `NoSuchFileException: /airbyte/tmp/tmpXXX.json`

Spawned source-postgres connector cannot find the config file PyAirbyte wrote. Root cause is one of:

1. **The host's `/tmp/airbyte/tmp` directory is missing.** Docker Desktop wipes `/tmp` on engine restart and macOS wipes it on reboot. The Jenkins container's ENTRYPOINT `mkdir -p`s it on every start, but if you bypassed that wrapper or are testing with a different image, recreate it manually:

   ```bash
   mkdir -p /tmp/airbyte/tmp && chmod 777 /tmp/airbyte/tmp
   ```

2. **The compose bind mount is asymmetric.** The compose file MUST mount `/tmp/airbyte:/tmp/airbyte` (same path both sides). When the runner Jenkins container tells the host docker daemon `docker run -v /tmp/airbyte/tmp:/airbyte/tmp ...`, the daemon resolves `/tmp/airbyte/tmp` against the **host filesystem** — it has no view of the runner container's bind translations. Asymmetric mounts (e.g. `runtime/airbyte:/tmp/airbyte`) silently produce empty connector mounts. See [Architecture > DinD Volume Sharing](architecture.md#dind-volume-sharing-for-pyairbyte) for the full rationale.

3. **The Jenkinsfile is missing `AIRBYTE_TEMP_DIR=/tmp/airbyte/tmp`.** Regenerate with the latest forge-cli:

   ```bash
   fluid generate ci --system jenkins --install-mode dev-source --runner-host-override host.docker.internal --no-publish-include-env
   ```

## Stage 10 Publish Fails With `fluid: error: unrecognized arguments: --env dev`

`fluid publish` does not accept `--env`. Older Jenkinsfiles generated with the default `--publish-include-env` emit it anyway and Stage 10 dies. Regenerate the Jenkinsfile with `--no-publish-include-env` (now the default in current forge-cli):

```bash
cd fluid/contracts/<your-contract>/
fluid generate ci --system jenkins --install-mode dev-source --runner-host-override host.docker.internal --no-publish-include-env
```

For the silver scenarios (A1/A2/B1/B2), the Jenkinsfiles live in `gitlab/path-*/variants/*/`. Regenerate from inside each variant dir and commit to that variant's git repo.

## B2 (or B1) dbt Build Fails With `Could not find profile named 'subscriber360_ai_*_v1'`

The AI-generated dbt projects bake the data product id into `dbt_project.yml`'s `profile:` field, so `config/dbt/profiles.yml` needs a matching named profile. The lab keeps these as YAML anchors:

```yaml
x-snowflake-output: &snowflake_default
  target: "{{ env_var('DBT_TARGET', 'snowflake') }}"
  outputs:
    snowflake: { ... }

telco: *snowflake_default
subscriber360_ai_external_v1: *snowflake_default
subscriber360_ai_generated_v1: *snowflake_default
```

When you onboard a new AI-generated dbt project, add a one-line alias next to the existing ones; no other changes needed.

## Pre-* Build Fails With `psycopg.OperationalError: connection ... port 5433 ... refused`

The lab source Postgres container (`snowflake-telco-postgres`) is not running. It hosts the `telco_source` database that pre-1 (dlt), pre-2 (Airbyte), and pre-3 (Meltano) ingest from. Start it:

```bash
docker compose -f deploy/docker/docker-compose.yml --env-file .env up -d postgres
```

After Docker Desktop restarts, only Jenkins + the catalogs stack come back automatically; you have to start `postgres` again. `task up` brings everything up in one shot.

## SnowflakeCache Validation Fails With `Field required: account, username, warehouse, database, role`

The Snowflake env vars are empty inside the Jenkins container. Most common cause: invoking compose directly without `--env-file .env`:

```bash
# WRONG — Snowflake creds resolve to empty
docker compose -f deploy/docker/docker-compose.yml up -d jenkins

# RIGHT
docker compose -f deploy/docker/docker-compose.yml --env-file .env up -d jenkins

# OR (always correct)
task jenkins:up
```

The compose file's `environment:` block uses YAML anchors that resolve `${SNOWFLAKE_ACCOUNT}` etc. at compose-startup time. Without `--env-file .env`, those expand to empty and override the values that `env_file: runtime/generated/fluid.local.env` would otherwise inject into the container.

## I Want The Shortest Demo Rescue Path

Use [Backup Demo](../fluid/demo/backup-demo.md). It keeps the story small and dependency-light.
