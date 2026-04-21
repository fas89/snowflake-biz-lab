# Troubleshooting

## Airflow Does Not Show The Generated DAGs

Confirm the demo workspaces were bootstrapped:

```bash
ls gitlab/path-a-telco-silver-product-demo gitlab/path-b-ai-telco-silver-import-demo
```

If either directory is missing, run:

```bash
task workspaces:bootstrap
```

Then recycle the core stack:

```bash
task down
task up
```

docker-compose mounts `./gitlab/path-a-telco-silver-product-demo` (for the greenfield/import DAGs) and `./gitlab/path-b-ai-telco-silver-import-demo` (for the AI DAGs) into Airflow by default. If you have pointed `FLUID_DEMO_GITLAB_WORKSPACE` or `FLUID_AI_GITLAB_WORKSPACE` at a non-default path in `.env`, make sure that path actually exists and contains the expected variant structure.

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
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ data-product-forge
```

## TestPyPI Install Feels Flaky

Use the same install shape the repo expects:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ data-product-forge
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

## The CLI Mentions `llm_models.json`

You may see a warning like this during `validate` or `plan`:

```text
Could not load model catalog ... llm_models.json
```

In the latest TestPyPI `data-product-forge` release, that warning can appear even when the contract workflow still succeeds.

If `validate`, `plan`, or `doctor` finishes successfully, you can continue with the demo. Treat it as a release quirk, not as an automatic stop signal.

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
