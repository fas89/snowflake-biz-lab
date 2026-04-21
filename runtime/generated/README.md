# Local Runtime Env Files

Put local, ignored runtime files here.

## Recommended Files

### Path Setup For The Launchpads

Use these local files to set your repo and workspace paths once, then source them before running the launchpads.

By default, the demo workspaces live INSIDE the lab repo at:

```text
LAB_REPO/gitlab
```

That directory is gitignored and bootstrapped from the tracked templates under `fluid/fixtures/workspaces/` via `task workspaces:bootstrap`.

For Mac, the quickest path is:

```bash
./scripts/setup_mac_launchpad.sh
source runtime/generated/launchpad.local.sh
task workspaces:bootstrap
```

`GREENFIELD_GITLAB_URL` / `EXISTING_DBT_GITLAB_URL` are optional overrides if you want to clone demo workspaces from a hosted GitLab instead of bootstrapping from templates. Leave them empty for the default local flow.

Tracked examples:

```text
runtime/generated/launchpad.local.sh.example
runtime/generated/launchpad.local.ps1.example
```

Ignored local copies:

```text
runtime/generated/launchpad.local.sh
runtime/generated/launchpad.local.ps1
```

### Live Secrets For Snowflake And DMM

```text
runtime/generated/fluid.local.env
```

Keep non-secret workspace settings such as `FLUID_DEMO_GITLAB_WORKSPACE` in `.env`, not here.

For the local Entropy / DMM stack, the normal refresh flow is:

```bash
task catalogs:up
task catalogs:bootstrap
```

That helper creates or reuses the local Entropy admin account and writes a fresh `DMM_API_KEY` into this file.

## Suggested Contents

```bash
SNOWFLAKE_ACCOUNT=your-account
SNOWFLAKE_USER=your-user
SNOWFLAKE_PRIVATE_KEY_PATH=/secure/path/to/snowflake_user_key.p8
SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=
SNOWFLAKE_OAUTH_TOKEN=
SNOWFLAKE_WAREHOUSE=your-authorized-warehouse
SNOWFLAKE_DATABASE=TELCO_LAB
SNOWFLAKE_ROLE=your-authorized-role
SNOWFLAKE_STAGE_SCHEMA=TELCO_STAGE_LOAD
SNOWFLAKE_FLUID_SCHEMA=TELCO_FLUID_DEMO
DMM_API_URL=http://localhost:8095
DMM_API_KEY=
```

Use the same authorized Snowflake role and warehouse here that you use in `.env`, unless you intentionally want the FLUID runtime to connect with different credentials.

Load it only when needed:

```bash
set -a
source runtime/generated/fluid.local.env
set +a
```
