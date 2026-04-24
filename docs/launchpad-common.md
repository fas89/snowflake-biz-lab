# Launchpad Common

Use this page as the one primary first-run path. It gives you the local paths, the visible clean-start commands, the app logins, the platform bring-up, and the Snowflake prep shared by both tracks.

## Run This Page In Order

1. Set up the local path file and load it into your shell.
2. Create local `.env` files and bootstrap the demo workspaces.
3. Fill in the local Snowflake and catalog config.
4. Run the destructive clean-start block when you want a true from-zero rerun.
5. Bring up the local apps.
6. Seed Snowflake staging and reapply metadata.
7. Continue to exactly one track launchpad.

## Local UI Login Defaults

Use the local files if you already changed them. Otherwise the default first-run logins are:

- DMM / Entropy: `admin@example.com` / `change_me`
- Airflow: `admin` / `change_me`
- Jenkins: `admin` / `change_me`
- dbt docs: no login

The source of truth for overrides is:

- `.env.catalogs` for DMM / Entropy
- `.env` for Airflow
- `.env` or `.env.jenkins` for Jenkins

`task catalogs:bootstrap` also refreshes `DMM_API_KEY`, `DMM_ODPS_LINEAGE_MODE=contract`, and `DMM_AUTO_APPROVE_ACCESS=true` in `runtime/generated/fluid.local.env` for the local sandbox. Bronze-to-Silver product dependencies are published through Entropy `Access` agreements generated from `consumes[]`; they are not mirrored as DMM SourceSystems.

Security defaults:

- local Docker ports bind to `127.0.0.1` by default
- keep that default for normal laptop runs
- set `LAB_BIND_ADDRESS=0.0.0.0` only for an intentional shared demo, and rotate the default local passwords first

## 1. Set Up Your Local Paths

### Mac

```bash
./scripts/setup_mac_launchpad.sh
source runtime/generated/launchpad.local.sh
printf '%s\n' "$LOCAL_REPOS_DIR"
printf '%s\n' "$LAB_REPO"
printf '%s\n' "$GREENFIELD_WORKSPACE"
```

If the detected paths are wrong:

```bash
./scripts/setup_mac_launchpad.sh "/absolute/path/to/your/local/repos" --force
source runtime/generated/launchpad.local.sh
```

### Windows

```powershell
Copy-Item runtime/generated/launchpad.local.ps1.example runtime/generated/launchpad.local.ps1 -Force
notepad .\runtime\generated\launchpad.local.ps1
. .\runtime\generated\launchpad.local.ps1
Write-Host $env:LAB_REPO
Write-Host $env:GREENFIELD_WORKSPACE
```

## 2. Create Local Config Files And Workspaces

### Mac

```bash
cd "$LAB_REPO"
./scripts/setup_local_demo.sh
task workspaces:bootstrap
```

### Windows

```powershell
Set-Location $env:LAB_REPO
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
if (-not (Test-Path .env.catalogs)) { Copy-Item .env.catalogs.example .env.catalogs }
if (-not (Test-Path .env.jenkins)) { Copy-Item .env.jenkins.example .env.jenkins }
task workspaces:bootstrap
```

What you should see now:

- `./gitlab/path-a-telco-silver-product-demo` exists
- `./gitlab/path-b-ai-telco-silver-import-demo` exists
- local `.env`, `.env.catalogs`, and `.env.jenkins` exist

## 3. Fill In The Local Config

Before you start Docker or any live FLUID commands:

- put working `SNOWFLAKE_*` values in `.env` for the Docker-based `task seed:*` and `task metadata:*` commands
- put the live Snowflake values you want FLUID to use in `runtime/generated/fluid.local.env`
- keep `FLUID_DEMO_GITLAB_WORKSPACE`, `FLUID_AI_GITLAB_WORKSPACE`, and `DEMO_WORKSPACES_DIR` blank unless you moved the workspaces away from `./gitlab/`

Important:

- `.env` powers the local containers
- `runtime/generated/fluid.local.env` powers the live `fluid` commands
- `.env.catalogs` controls the DMM bootstrap login
- `.env.jenkins` is only for Jenkins overrides

## 4. Clean Start From Zero

Run this when you want the first-run state again: empty Jenkins, empty Airflow, reset catalogs, and fresh demo workspaces.

### Mac

```bash
source "$LAB_REPO/runtime/generated/launchpad.local.sh"
cd "$LAB_REPO"
python3 scripts/reset_demo_state.py --lab-repo "$LAB_REPO" --yes
docker compose -f deploy/docker/docker-compose.yml --env-file .env --profile jenkins down -v --remove-orphans
task catalogs:reset
rm -rf "$LAB_REPO/airflow/dags/active/current"
mkdir -p "$LAB_REPO/airflow/dags/active"
```

### Windows

```powershell
. "$env:LAB_REPO\runtime\generated\launchpad.local.ps1"
Set-Location $env:LAB_REPO
py -3 scripts/reset_demo_state.py --lab-repo $env:LAB_REPO --yes
docker compose -f deploy/docker/docker-compose.yml --env-file .env --profile jenkins down -v --remove-orphans
task catalogs:reset
Remove-Item "$env:LAB_REPO\airflow\dags\active\current" -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path "$env:LAB_REPO\airflow\dags\active" | Out-Null
```

Why this block matters:

- `reset_demo_state.py` wipes generated demo artifacts and re-bootstraps `./gitlab/`
- `docker compose ... down -v` deletes the persisted Jenkins, Airflow, and Postgres state
- `task catalogs:reset` removes the local DMM data and stale API key
- clearing `airflow/dags/active/current` guarantees Airflow starts with no scenario DAGs

## 5. Bring Up The Local Apps

### Mac

```bash
cd "$LAB_REPO"
task up
task catalogs:up
task catalogs:bootstrap
task preflight
task jenkins:up
task ps
```

### Windows

```powershell
Set-Location $env:LAB_REPO
task up
task catalogs:up
task catalogs:bootstrap
task preflight
task jenkins:up
task ps
```

What you should see now:

- Airflow opens at [http://localhost:8085](http://localhost:8085) and shows no scenario DAGs yet
- Jenkins opens at [http://localhost:8081](http://localhost:8081) and shows no A1 or A2 jobs yet
- DMM opens at [http://localhost:8095](http://localhost:8095) and accepts the bootstrap login above
- dbt docs opens at [http://localhost:8086](http://localhost:8086), but the silver docs are not meaningful until you refresh them for A1 or A2
- Mailpit opens at [http://localhost:8026](http://localhost:8026) if you want to inspect local catalog signup email

Useful local URLs:

- Airflow: [http://localhost:8085](http://localhost:8085)
- dbt docs: [http://localhost:8086](http://localhost:8086)
- Jenkins: [http://localhost:8081](http://localhost:8081)
- Entropy / DMM: [http://localhost:8095](http://localhost:8095)
- Mailpit: [http://localhost:8026](http://localhost:8026)

## 6. Seed Snowflake Staging And Metadata

### Mac

```bash
cd "$LAB_REPO"
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
task seed:reset:confirm
task seed:generate
task seed:load
task seed:verify
task metadata:apply
task metadata:verify
```

What you should see now:

- Snowflake landing tables exist in `SNOWFLAKE_STAGE_SCHEMA`
- Horizon metadata is back on the source objects
- Jenkins is still empty
- Airflow is still empty

## 7. Continue To One Track

Choose exactly one:

- [Demo Release Launchpad (Mac)](demo-release-launchpad-mac.md)
- [Demo Release Launchpad (Windows)](demo-release-launchpad-windows.md)
- [Dev Source Launchpad (Mac)](dev-source-launchpad-mac.md)
- [Dev Source Launchpad (Windows)](dev-source-launchpad-windows.md)

Then run Bronze, A1, and A2 from the matching playbook:

- [Variant Playbook (Mac)](variant-playbook-mac.md)
- [Variant Playbook (Windows)](variant-playbook-windows.md)

## Related Docs

- [Launchpad Recovery](launchpad-recovery.md)
- [Credentials](credentials.md)
- [Scenario Validation Matrix](scenario-validation-matrix.md)
- [Jenkins SCM Handoff](jenkins-scm-handoff.md)
- [Command Reference](command-reference.md)
- [FLUID Gap Register](fluid-gap-register.md)
