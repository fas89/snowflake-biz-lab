# Credentials

This repo keeps secrets out of tracked contracts and out of checked-in configuration.

## Two Files, Two Responsibilities

### `.env`

Use `.env` for non-secret local settings, especially:

- `FLUID_DEMO_GITLAB_WORKSPACE`
- local port overrides
- local Docker defaults
- GitLab project URL placeholders

For the local Airflow bridge, `FLUID_DEMO_GITLAB_WORKSPACE` should be an absolute macOS path to the active GitLab working copy. Example:

```text
FLUID_DEMO_GITLAB_WORKSPACE=/Users/A200004702/gitlab/telco-silver-product-demo
```

### `runtime/generated/fluid.local.env`

Use this ignored file for live Snowflake and DMM secrets.

```text
runtime/generated/fluid.local.env
```

Load it only when you are about to run live FLUID commands:

```bash
set -a
source runtime/generated/fluid.local.env
set +a
```

The sample outline lives in [runtime/generated/README.md](../runtime/generated/README.md).

## The Runtime Rule

`fluid apply` and `fluid dmm publish` should read secrets from environment variables only.

Do not put secrets in:

- `contract.fluid.yaml`
- `.gitlab-ci.yml`
- `Jenkinsfile`
- plan snapshots
- screenshots

## Snowflake Auth Preference

Use Snowflake auth in this order for automation:

1. key-pair auth via `SNOWFLAKE_PRIVATE_KEY_PATH`
2. OAuth via `SNOWFLAKE_OAUTH_TOKEN`
3. password auth only as a local/manual fallback

Keep these values ready for live runs:

- `SNOWFLAKE_ACCOUNT`
- `SNOWFLAKE_USER`
- `SNOWFLAKE_PRIVATE_KEY_PATH` or `SNOWFLAKE_OAUTH_TOKEN`
- `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` when needed
- `SNOWFLAKE_WAREHOUSE`
- `SNOWFLAKE_DATABASE`
- `SNOWFLAKE_ROLE`
- `SNOWFLAKE_STAGE_SCHEMA`
- `SNOWFLAKE_FLUID_SCHEMA`

## Data Mesh Manager

For local Entropy / DMM publication, keep these in `runtime/generated/fluid.local.env`:

- `DMM_API_URL`
- `DMM_API_KEY`

The repo defaults the local API URL to `http://localhost:8095`, but the API key should still be injected only at runtime.

## Hosted GitLab

When you move the demo into hosted GitLab CI:

- store secrets as protected and masked CI variables
- keep generated CI YAML free of secret values
- inject secrets only into the runtime job environment

## Jenkins

When you use Jenkins:

- store Snowflake and DMM secrets in Jenkins Credentials
- bind them into environment variables at job runtime
- keep the tracked `Jenkinsfile` secret-free

## Security Notes

- Never commit `runtime/generated/fluid.local.env`
- Prefer separate demo credentials from day-to-day engineering credentials
- Rotate demo keys after public sessions
