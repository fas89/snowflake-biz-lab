# Troubleshooting

## Airflow Does Not Show The Generated DAGs

Check `.env` first.

`FLUID_DEMO_GITLAB_WORKSPACE` must point to the active GitLab working copy as an absolute macOS path.

Example:

```text
FLUID_DEMO_GITLAB_WORKSPACE=/Users/A200004702/gitlab/telco-silver-product-demo
```

Then recycle the core stack:

```bash
task down
task up
```

If you switch from the greenfield demo to the existing-dbt demo, update the path and restart the Airflow stack again.

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
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ data-product-forge==0.7.10
```

## TestPyPI Install Feels Flaky

Use the same install shape the repo expects:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ data-product-forge==0.7.10
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

## I Installed `0.7.10`, But The Contract Still Says `0.7.2`

That is expected in this repo. Read [CLI Version vs `fluidVersion`](fluid-versions.md).

## The CLI Mentions `llm_models.json`

You may see a warning like this during `validate` or `plan`:

```text
Could not load model catalog ... llm_models.json
```

In the current `data-product-forge==0.7.10` release, that warning can appear even when the contract workflow still succeeds.

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

## `fluid dmm publish` Fails

Check the runtime env file first:

```bash
set -a
source runtime/generated/fluid.local.env
set +a
```

Then confirm:

- `DMM_API_URL` points to your local Entropy stack, usually `http://localhost:8095`
- `DMM_API_KEY` is present
- the Entropy UI opens at [http://localhost:8095](http://localhost:8095)

## Telco Contract Fails Because Stage Tables Are Missing

The telco FLUID contract expects seeded landing tables to already exist.

Prepare them before the live apply:

```bash
task up
task seed:generate
task seed:load
```

## `fluid generate ci --system jenkins` Creates A File, But Jenkins Does Not Automatically Run It

That behavior belongs in the [FLUID Gap Register](fluid-gap-register.md). The repo documents the target end-state story, but current Jenkins handoff work is intentionally tracked as future FLUID implementation work.

## I Want The Shortest Demo Rescue Path

Use [Backup Demo](../fluid/demo/backup-demo.md). It keeps the story small and dependency-light.
