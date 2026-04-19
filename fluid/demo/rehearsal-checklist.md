# Rehearsal Checklist

Use this before demo day so you know which steps are off-stage prep, which ones are live on-stage moments, and which ones are tracked as FLUID gaps.

| Step | Type | Notes |
| --- | --- | --- |
| Copy `.env`, `.env.catalogs`, and `.env.jenkins` | Off-stage prep | Set `FLUID_DEMO_GITLAB_WORKSPACE` before starting Airflow |
| Create `runtime/generated/fluid.local.env` | Off-stage prep | Keep only Snowflake and DMM secrets here |
| Clone `$LOCAL_REPOS_DIR/gitlab/telco-silver-product-demo` | Off-stage prep | Greenfield workspace |
| Clone `$LOCAL_REPOS_DIR/gitlab/telco-silver-import-demo` | Off-stage prep | Existing dbt workspace |
| `task up` | Live on-stage step | You can show Airflow coming up |
| `task jenkins:up` | Live on-stage step | Jenkins URL should be ready |
| `task catalogs:up` | Live on-stage step | Entropy / DMM and MailHog should be reachable |
| `task catalogs:bootstrap` | Live on-stage step | Local Entropy login and `DMM_API_KEY` should be ready before the publish step |
| `task seed:reset` | Live on-stage step | Drops the full demo database so the Snowflake landing path visibly starts from a clean state |
| `task seed:generate` | Live on-stage step | Makes the data story concrete |
| `task seed:load` | Live on-stage step | Loads Snowflake staging |
| `task seed:verify` | Live on-stage step | Confirms the landing schema is ready |
| `task metadata:apply` | Live on-stage step | Applies schema, table, and column comments for Horizon |
| `task metadata:verify` | Live on-stage step | Verifies schema, table, and column comments |
| Install the latest `data-product-forge` release in the GitLab workspace | Live on-stage step | Shows the released CLI |
| `fluid init` | Live on-stage step | Starts the workspace in GitLab |
| `fluid forge` | Live on-stage step | AI-authored silver contract moment |
| `fluid import` | Live on-stage step | Existing dbt variation |
| `fluid generate schedule --scheduler airflow` | Live on-stage step | Airflow artifact generation |
| `fluid generate ci --system jenkins` | Live on-stage step | Jenkins artifact generation |
| `fluid validate` | Live on-stage step | Contract correctness checkpoint |
| `fluid plan --out runtime/plan.json --html` | Live on-stage step | Plan JSON plus HTML view |
| `fluid apply --yes --report runtime/apply_report.html` | Live on-stage step | Deployment moment |
| `fluid generate standard --format opds|odcs|odps` | Live on-stage step | Standards export close |
| `fluid publish --catalog entropy-local` | Live on-stage step | Marketplace close through the local catalog alias |
| `apply -> Jenkins handoff` | Future FLUID gap | See [FLUID Gap Register](../../docs/fluid-gap-register.md) |
| deterministic Snowflake silver `forge` flow | Future FLUID gap | See [FLUID Gap Register](../../docs/fluid-gap-register.md) |
| stronger import-to-enrichment dbt flow | Future FLUID gap | See [FLUID Gap Register](../../docs/fluid-gap-register.md) |
| smoother Airflow workspace detection | Future FLUID gap | See [FLUID Gap Register](../../docs/fluid-gap-register.md) |
| standards-to-marketplace handoff | Future FLUID gap | See [FLUID Gap Register](../../docs/fluid-gap-register.md) |
