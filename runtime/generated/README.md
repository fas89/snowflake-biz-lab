# Local Runtime Env Files

Put local, ignored runtime files here.

## Recommended File

```text
runtime/generated/fluid.local.env
```

Keep non-secret workspace settings such as `FLUID_DEMO_GITLAB_WORKSPACE` in `.env`, not here.

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
