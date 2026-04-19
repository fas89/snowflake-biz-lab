# Local Runtime Env Files

Put local, ignored runtime files here.

## Recommended Files

### Path Setup For The Launchpads

Use these local files to set your repo and workspace paths once, then source them before running the launchpads.

By default, the demo workspaces live under:

```text
LOCAL_REPOS_DIR/gitlab
```

For Mac, the quickest path is:

```bash
./scripts/setup_mac_launchpad.sh
source runtime/generated/launchpad.local.sh
```

If you plan to run the clone step from the launchpads, also set these in your local launchpad file:

```bash
GREENFIELD_GITLAB_URL
EXISTING_DBT_GITLAB_URL
```

If you leave those values empty, skip the `git clone` step in the docs and create the workspaces some other way.

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
SNOWFLAKE_WAREHOUSE=TELCO_TRANSFORM_WH
SNOWFLAKE_DATABASE=TELCO_LAB
SNOWFLAKE_ROLE=TRANSFORMER
SNOWFLAKE_STAGE_SCHEMA=TELCO_STAGE_LOAD
SNOWFLAKE_FLUID_SCHEMA=TELCO_FLUID_DEMO
DMM_API_URL=http://localhost:8095
DMM_API_KEY=
```

Load it only when needed:

```bash
set -a
source runtime/generated/fluid.local.env
set +a
```
