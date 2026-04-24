# Launchpad Recovery

Quick resets for the failures that happen most often during a rehearsal.

## Start Here

Run `task preflight` first. It checks bind mounts, DMM API key health, and bronze catalog presence, and it auto-heals where it safely can.

## DMM Publish Succeeded But Nothing Appears In DMM

### Mac

```bash
cd "$LAB_REPO"
task catalogs:up
task catalogs:bootstrap
```

### Windows

```powershell
Set-Location $env:LAB_REPO
task catalogs:up
task catalogs:bootstrap
```

If the DMM UI still looks wrong, do a full catalog reset and re-run the scenario publishes:

For Silver lineage, check DMM Access agreements as the source of truth. Product-to-product Bronze dependencies should appear as approved Access edges, not as duplicated SourceSystem nodes or ODPS input ports on the Silver product.

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

## `fluid publish` Fails With A Catalog Health Error

Reload the bootstrap state and your secrets file, then retry the same `publish` command.

### Mac

```bash
cd "$LAB_REPO"
task catalogs:bootstrap
source runtime/generated/launchpad.local.sh
set -a
source "$FLUID_SECRETS_FILE"
set +a
```

### Windows

```powershell
Set-Location $env:LAB_REPO
task catalogs:bootstrap
. .\runtime\generated\launchpad.local.ps1
Get-Content $env:FLUID_SECRETS_FILE | ForEach-Object { if ($_ -match '^(?!#)([^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
```

## Jenkins Job Is Missing Or Still Points At Old Config

Re-run the on-demand sync for the scenario. This is the supported way to create or refresh the job definition.

### Mac

```bash
cd "$LAB_REPO"
task jenkins:sync SCENARIO=A1
task jenkins:sync SCENARIO=A2
task jenkins:build SCENARIO=A1
task jenkins:build SCENARIO=A2
```

### Windows

```powershell
Set-Location $env:LAB_REPO
task jenkins:sync SCENARIO=A1
task jenkins:sync SCENARIO=A2
task jenkins:build SCENARIO=A1
task jenkins:build SCENARIO=A2
```

If Jenkins itself looks unhealthy, restart it and sync again:

```bash
task jenkins:down
task jenkins:up
```

## Airflow Still Shows The Wrong DAGs

Clear the active destination and rerun the native FLUID sync from the scenario directory.

### Mac

```bash
rm -rf "$LAB_REPO/airflow/dags/active/current"
"$FLUID_CLI" schedule-sync --scheduler airflow --dags-dir ../../reference-assets/airflow_subscriber360/dags --destination "$LAB_REPO/airflow/dags/active/current"
```

### Windows

```powershell
Remove-Item "$env:LAB_REPO\airflow\dags\active\current" -Recurse -Force -ErrorAction SilentlyContinue
& $env:FLUID_CLI schedule-sync --scheduler airflow --dags-dir ..\..\reference-assets\airflow_subscriber360\dags --destination "$env:LAB_REPO\airflow\dags\active\current"
```

## `fluid apply` Failed Partway Through

Reload the runtime secrets and retry the same explicit apply command.

### Mac

```bash
cd "$WORKSPACE_PATH_FROM_YOUR_SCENARIO"
set -a
source "$FLUID_SECRETS_FILE"
set +a
"$FLUID_CLI" apply contract.fluid.yaml --mode amend-and-build --build "$BUILD_ID" --yes --report runtime/apply_report.html
```

### Windows

```powershell
Set-Location $env:WORKSPACE_PATH_FROM_YOUR_SCENARIO
Get-Content $env:FLUID_SECRETS_FILE | ForEach-Object { if ($_ -match '^(?!#)([^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
& $env:FLUID_CLI apply contract.fluid.yaml --mode amend-and-build --build $buildId --yes --report runtime/apply_report.html
```

## Full Reset

This is the visible clean-start path from the quickstart, followed by platform bring-up and Snowflake prep.

### Mac

```bash
cd "$LAB_REPO"
python3 scripts/reset_demo_state.py --lab-repo "$LAB_REPO" --yes
docker compose -f deploy/docker/docker-compose.yml --env-file .env --profile jenkins down -v --remove-orphans
task catalogs:reset
rm -rf "$LAB_REPO/airflow/dags/active/current"
mkdir -p "$LAB_REPO/airflow/dags/active"
task up
task catalogs:up
task catalogs:bootstrap
task preflight
task jenkins:up
task seed:reset:confirm
task seed:generate
task seed:load
task seed:verify
task metadata:apply
task metadata:verify
```

### Windows

```powershell
Set-Location $env:LAB_REPO
py -3 scripts/reset_demo_state.py --lab-repo $env:LAB_REPO --yes
docker compose -f deploy/docker/docker-compose.yml --env-file .env --profile jenkins down -v --remove-orphans
task catalogs:reset
Remove-Item "$env:LAB_REPO\airflow\dags\active\current" -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path "$env:LAB_REPO\airflow\dags\active" | Out-Null
task up
task catalogs:up
task catalogs:bootstrap
task preflight
task jenkins:up
task seed:reset:confirm
task seed:generate
task seed:load
task seed:verify
task metadata:apply
task metadata:verify
```

## Related Docs

- [Launchpad Common](launchpad-common.md)
- [Scenario Validation Matrix](scenario-validation-matrix.md)
- [Jenkins SCM Handoff](jenkins-scm-handoff.md)
- [Troubleshooting](troubleshooting.md)
