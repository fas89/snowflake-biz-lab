# Launchpad Recovery

Quick resets for the failures that happen most often on a live rehearsal. Each block is self-contained — pick the row that matches what broke.

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
