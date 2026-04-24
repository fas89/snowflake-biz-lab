# Launchpad Recovery

Quick resets for the failures that happen most often on a live rehearsal. Each block is self-contained — pick the row that matches what broke.

**Start here:** `task preflight` runs three self-healing health checks (Docker bind-mounts, DMM API key validity, bronze catalog presence) and often fixes the root cause without the rest of this page. Run it first when anything breaks; the sections below cover what to do when preflight cannot self-heal.

In the examples below, `$FLUID_CLI` resolves to whatever launch binary your track uses:

- `demo-release`: the `fluid` executable inside the active workspace venv
- `dev-source`: `$FLUID_DEV_BIN` (Mac) or `$env:FLUID_DEV_BIN` (Windows)

## DMM Publish Succeeded But Nothing Appears At `http://localhost:8095`

Usually the API key in `runtime/generated/fluid.local.env` is stale or the catalog stack was never bootstrapped. Refresh both:

### Mac

```bash
cd "$LAB_REPO"
task catalogs:up
task catalogs:bootstrap
# then re-run the failing `fluid publish` command
```

### Windows

```powershell
Set-Location $env:LAB_REPO
task catalogs:up
task catalogs:bootstrap
# then re-run the failing `fluid publish` command
```

If the UI still shows nothing, do a clean catalog reset and re-run every publish from the start of the scenario:

### Mac

```bash
cd "$LAB_REPO"
task catalogs:reset
task catalogs:up
task catalogs:bootstrap
```

### Windows

```powershell
Set-Location $env:LAB_REPO
task catalogs:reset
task catalogs:up
task catalogs:bootstrap
```

## `fluid publish` Fails With "Catalog Health Check Failed - Endpoint Not Accessible"

The Entropy stack at [http://localhost:8095](http://localhost:8095) is up, but `fluid publish` reports `❌ Failed | Catalog health check failed - endpoint not accessible`. There are two common root causes:

1. **Missing `DMM_API_KEY` in `runtime/generated/fluid.local.env`** — Entropy returns 403 on the health-check call and the CLI renders it as "not accessible". `task preflight` detects this and auto-heals by re-running `bootstrap_entropy_local.py`.
2. **`FLUID_SECRETS_FILE` not exported in the current shell** — forge-cli's `hydrate_dotenv` loads project `.env` with `override=True`, so the empty `DMM_API_KEY=` placeholder in `.env` clobbers the value you sourced manually. Sourcing `runtime/generated/launchpad.local.sh` exports `FLUID_SECRETS_FILE`, which lets forge-cli restore the real key after the `.env` clobber.

The quickest fix tries both — re-bootstrap the catalog stack to mint a fresh key, re-source the launchpad, and retry:

### Mac

```bash
cd "$LAB_REPO"
task catalogs:bootstrap
source runtime/generated/launchpad.local.sh
set -a
source "$FLUID_SECRETS_FILE"
set +a
# then re-run the failing `fluid publish` command
```

### Windows

```powershell
Set-Location $env:LAB_REPO
task catalogs:bootstrap
. .\runtime\generated\launchpad.local.ps1
Get-Content $env:FLUID_SECRETS_FILE | ForEach-Object { if ($_ -match '^(?!#)([^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
# then re-run the failing `fluid publish` command
```

`task catalogs:bootstrap` provisions the admin user, rewrites `DMM_API_KEY` in `runtime/generated/fluid.local.env`, and refreshes `~/.fluid/config.yaml` so the next `fluid publish` sends a valid `x-api-key` header. Sourcing `launchpad.local.sh` exports `FLUID_SECRETS_FILE` so forge-cli's `hydrate_dotenv` can recover after it loads project `.env`.

Prefer `task publish:bronze` for bronze publishes — it exports `FLUID_SECRETS_FILE` itself and is robust to the shell state above.

## Jenkins Did Not Pick Up The Jenkinsfile

The CasC pipelines read from `/workspace/gitlab/` (the workspace folder on disk, not a GitLab remote). Reprovision so CasC rescans:

### Mac

```bash
cd "$LAB_REPO"
task jenkins:down
task jenkins:up
```

### Windows

```powershell
Set-Location $env:LAB_REPO
task jenkins:down
task jenkins:up
```

Then reopen [http://localhost:8081](http://localhost:8081) and click **Scan Multibranch Pipeline Now** on the affected job.

## `fluid apply` Failed Partway Through (Auth, Role, Or Adapter Error)

Reload Snowflake secrets into the current shell and retry the same `apply` command — the build is idempotent for the demo-scoped schema.

### Mac

```bash
cd "$WORKSPACE_PATH_FROM_YOUR_SCENARIO"
set -a
source "$FLUID_SECRETS_FILE"
set +a
"$FLUID_CLI" apply contract.fluid.yaml --build "$BUILD_ID" --yes --report runtime/apply_report.html
```

### Windows

```powershell
Set-Location $env:WORKSPACE_PATH_FROM_YOUR_SCENARIO
Get-Content $env:FLUID_SECRETS_FILE | ForEach-Object { if ($_ -match '^(?!#)([^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
& $env:FLUID_CLI apply contract.fluid.yaml --build $buildId --yes --report runtime/apply_report.html
```

If auth is the root cause, open `runtime/generated/fluid.local.env` and confirm the `SNOWFLAKE_*` values are current. The Docker seed tasks read `.env` instead, so the two files can drift.

## dbt Docs Refresh Or Airflow DAG Listing Sees An Empty `/workspace/greenfield/`

Symptom on `task dbt:docs:refresh SCENARIO=A1`:

```text
Error: Invalid value for '--project-dir': Path '/workspace/greenfield/reference-assets/dbt_dv2_subscriber360' does not exist.
```

Or Airflow does not list the expected DAG even though the `.py` file is present on disk at the expected workspace path. macOS Docker Desktop bind mounts can drift after a long-running container — `docker exec <container> ls /workspace/greenfield/` returns empty while the host directory is populated. Restart the affected services so the mount rehydrates from the current host state:

### Mac

```bash
cd "$LAB_REPO"
docker compose -f deploy/docker/docker-compose.yml --env-file .env restart dbt-runner airflow-webserver airflow-scheduler
```

### Windows

```powershell
Set-Location $env:LAB_REPO
docker compose -f deploy/docker/docker-compose.yml --env-file .env restart dbt-runner airflow-webserver airflow-scheduler
```

Re-run `task dbt:docs:refresh SCENARIO=<A1|A2>` (and re-list Airflow DAGs) after ~10 seconds. The root cause is macOS-specific: `fakeowner` bind mounts lose visibility into host-side changes made after container start; a restart rebinds cleanly.

## Full Reset (When You Need A Guaranteed Clean Rerun)

Runs the destructive reset from [Launchpad Common: Clean Start First](launchpad-common.md#clean-start-first) and then re-runs platform bring-up and data prep:

### Mac

```bash
cd "$LAB_REPO"
python3 scripts/reset_demo_state.py --lab-repo "$LAB_REPO" --yes
task down && task jenkins:down && task catalogs:reset
task up && task jenkins:up && task catalogs:up && task catalogs:bootstrap
task workspaces:reset
task seed:reset:confirm && task seed:generate && task seed:load && task seed:verify
task metadata:apply && task metadata:verify
```

### Windows

```powershell
Set-Location $env:LAB_REPO
py -3 scripts/reset_demo_state.py --lab-repo $env:LAB_REPO --yes
task down; task jenkins:down; task catalogs:reset
task up; task jenkins:up; task catalogs:up; task catalogs:bootstrap
task workspaces:reset
task seed:reset:confirm; task seed:generate; task seed:load; task seed:verify
task metadata:apply; task metadata:verify
```

Then restart your track launchpad from its **Bootstrap Runtime** section.

## Related Docs

- [Launchpad Common](launchpad-common.md)
- [Plan Verification Checklist](plan-verification-checklist.md)
- [Troubleshooting](troubleshooting.md)
