# Launchpad Common

Use this page for the setup that both launchpads share.
Run it top to bottom before you switch into a platform-specific track.

Important:

- Copy only the lines inside the code blocks.
- Do not copy the leading `````bash````` or `````powershell````` fence lines into your shell.
- The shell blocks below are written to be paste-safe in macOS `zsh`.

## Clean Start First

If you want the demo to be reproducible from a fresh local state, do this before anything else.

This is the fastest safe sequence:

- regenerate the local path file from the repo location
- load the path variables into your shell
- reset generated demo state
- stop the local Docker stacks so the next bring-up starts clean

### Mac

```bash
./scripts/setup_mac_launchpad.sh --force
source runtime/generated/launchpad.local.sh
cd "$LAB_REPO"
python3 scripts/reset_demo_state.py --lab-repo "$LAB_REPO" --greenfield-workspace "$GREENFIELD_WORKSPACE" --existing-workspace "$EXISTING_DBT_WORKSPACE" --yes
task down
task jenkins:down
task catalogs:reset
```

### Windows

```powershell
Copy-Item runtime/generated/launchpad.local.ps1.example runtime/generated/launchpad.local.ps1 -Force
notepad .\runtime\generated\launchpad.local.ps1
. .\runtime\generated\launchpad.local.ps1
Set-Location $env:LAB_REPO
py -3 scripts/reset_demo_state.py --lab-repo $env:LAB_REPO --greenfield-workspace $env:GREENFIELD_WORKSPACE --existing-workspace $env:EXISTING_DBT_WORKSPACE
task down
task jenkins:down
task catalogs:reset
```

If you run the clean-start block above, skip section 1 and continue with section 2 below.

The reset script cleans files and folders. The `source runtime/generated/launchpad.local.sh` step is what refreshes the current shell variables.

## Run This Page In Order

1. Set up your local path variables.
2. Run the one-time local setup helper.
3. Fill in the local config and secret files.
4. Start the local Docker applications.
5. Open the browser tabs.
6. Find the app credentials and login values.
7. Run the off-stage Snowflake seed and metadata prep.
8. Continue to exactly one track-specific launchpad, then switch into the matching workspace README for the variant you want to run.

If you are starting fresh, run the clean-start block above, then continue with steps 2 through 8.

If you are not doing a full clean restart, skip the clean-start block above and run steps 1 through 8.

## 1. Set Up Your Local Paths First

The easiest setup is to keep your local repos under one parent folder and store the path variables in one local file.

If your machine looks like this:

- `<LOCAL_REPOS_DIR>/snowflake-biz-lab`
- `<LOCAL_REPOS_DIR>/forge-cli`

then you only need to customize `LOCAL_REPOS_DIR` in the local launchpad file below.

### Mac

Run this from the repo root.

This block:

- generates the local path file if it does not exist yet
- loads the path variables into the current shell
- creates the parent workspace folder
- prints the two most important path variables so you can sanity-check them

```bash
./scripts/setup_mac_launchpad.sh
source runtime/generated/launchpad.local.sh
mkdir -p "$DEMO_WORKSPACES_DIR"
printf '%s\n' "$LOCAL_REPOS_DIR"
printf '%s\n' "$LAB_REPO"
```

If the detected paths are wrong or your repos live somewhere else, regenerate the file with the parent folder you want:

```bash
./scripts/setup_mac_launchpad.sh "/absolute/path/to/your/local/repos" --force
source runtime/generated/launchpad.local.sh
```

If you still want to tweak a path after that, edit `runtime/generated/launchpad.local.sh` directly.

### Windows

This block:

- creates your local launchpad file from the example
- lets you review or edit the paths
- loads the variables into the current PowerShell session
- creates the parent workspace folder
- prints the key repo path so you can verify it

```powershell
Copy-Item runtime/generated/launchpad.local.ps1.example runtime/generated/launchpad.local.ps1
notepad .\runtime\generated\launchpad.local.ps1
. .\runtime\generated\launchpad.local.ps1
New-Item -ItemType Directory -Force $env:DEMO_WORKSPACES_DIR | Out-Null
$env:LOCAL_REPOS_DIR
Write-Host $env:LAB_REPO
```

These local files are gitignored, so each operator can keep personal paths without affecting the repo.

## 2. Run The One-Time Local Setup

The safest path is to use the helper script below.

Do not run raw `git clone "$GREENFIELD_GITLAB_URL" ...` or `git clone "$EXISTING_DBT_GITLAB_URL" ...` commands unless you have already set both GitLab URL variables in your local launchpad file.

Before cloning from the repo, set `GREENFIELD_GITLAB_URL` and `EXISTING_DBT_GITLAB_URL` in your local launchpad file.

If either GitLab URL is still empty, the helper will skip that clone instead of failing.

This step prepares your local working area:

- creates local `.env` files only if they do not already exist
- clones the GitLab workspaces only when the URLs are set
- otherwise creates or keeps the local workspace folders so the rest of the demo can continue
- keeps the checked-in workspace scaffolds if they are already present on disk

### Mac

```bash
cd "$LAB_REPO"
./scripts/setup_local_demo.sh
```

### Windows

```powershell
Set-Location $env:LAB_REPO
Copy-Item .env.example .env
Copy-Item .env.catalogs.example .env.catalogs
Copy-Item .env.jenkins.example .env.jenkins
if ($env:GREENFIELD_GITLAB_URL) { git clone $env:GREENFIELD_GITLAB_URL $env:GREENFIELD_WORKSPACE } else { New-Item -ItemType Directory -Force $env:GREENFIELD_WORKSPACE | Out-Null; Write-Host "Set GREENFIELD_GITLAB_URL in runtime/generated/launchpad.local.ps1 before cloning the greenfield workspace." }
if ($env:EXISTING_DBT_GITLAB_URL) { git clone $env:EXISTING_DBT_GITLAB_URL $env:EXISTING_DBT_WORKSPACE } else { New-Item -ItemType Directory -Force $env:EXISTING_DBT_WORKSPACE | Out-Null; Write-Host "Set EXISTING_DBT_GITLAB_URL in runtime/generated/launchpad.local.ps1 before cloning the existing-dbt workspace." }
```

## 3. Fill In Your Local Config Files

In `.env`, set:

```text
FLUID_DEMO_GITLAB_WORKSPACE=/absolute/path/to/telco-silver-product-demo
FLUID_AI_GITLAB_WORKSPACE=/absolute/path/to/telco-silver-import-demo
```

Create or update:

```text
$LAB_REPO/runtime/generated/fluid.local.env
```

The most important local files are:

- `.env` for local application settings
- `.env.catalogs` for the local Entropy / DMM stack
- `.env.jenkins` for Jenkins-specific overrides
- `runtime/generated/fluid.local.env` for Snowflake runtime secrets and the generated DMM API key

Before you continue, make sure:

- `.env` points `FLUID_DEMO_GITLAB_WORKSPACE` at your greenfield workspace
- `.env` points `FLUID_AI_GITLAB_WORKSPACE` at your AI/import workspace
- `.env` contains working `SNOWFLAKE_*` values for the Docker-based `task seed:*` and `task metadata:*` commands
- `runtime/generated/fluid.local.env` contains the Snowflake secrets you want the live demo to use
- `task catalogs:bootstrap` will fill or refresh `DMM_API_KEY` for you after the catalog stack starts

Important:

- Step 7 will not work until valid Snowflake credentials are present in `.env`
- the off-stage seed and metadata tasks run inside Docker, so they read Snowflake auth from `.env`, not from `runtime/generated/fluid.local.env`

## 4. Start The Local Applications

Bring up the local Docker applications before opening any of the UI links below.

This block:

- starts the core platform services
- starts the local dbt docs UI
- starts Jenkins
- starts the catalog stack
- completes the local Entropy bootstrap flow in the background
- shows the resulting container state

### Mac

```bash
cd "$LAB_REPO"
task up
task jenkins:up
task catalogs:up
task catalogs:bootstrap
task ps
```

### Windows

```powershell
Set-Location $env:LAB_REPO
task up
task jenkins:up
task catalogs:up
task catalogs:bootstrap
task ps
```

## 5. Open The Browser Tabs

- Airflow: [http://localhost:8085](http://localhost:8085)
- dbt docs: [http://localhost:8086](http://localhost:8086)
- Jenkins: [http://localhost:8081](http://localhost:8081)
- Entropy / DMM: [http://localhost:8095](http://localhost:8095)
- MailHog: [http://localhost:8026](http://localhost:8026)

## 6. Find The App Credentials

Before you sign in to the local applications, check these local files:

- `.env` for Airflow and the default Jenkins login
- `.env.jenkins` for Jenkins-specific overrides
- `.env.catalogs` for the Entropy / DMM bootstrap login
- `runtime/generated/fluid.local.env` for Snowflake runtime secrets and the generated DMM API key used by the demo commands

The quickest full reference is [Credentials](credentials.md).

For the local apps, the important values are:

- Airflow login: `AIRFLOW_ADMIN_USER` and `AIRFLOW_ADMIN_PASSWORD` in `.env`
- Jenkins login: `JENKINS_ADMIN_ID` and `JENKINS_ADMIN_PASSWORD` in `.env` or `.env.jenkins`
- Entropy / DMM login: `ENTROPY_BOOTSTRAP_ADMIN_EMAIL` and `ENTROPY_BOOTSTRAP_ADMIN_PASSWORD` in `.env.catalogs`
- DMM API key: `task catalogs:bootstrap` refreshes `DMM_API_KEY` in `runtime/generated/fluid.local.env`
- dbt docs UI: no login by default

These files are gitignored, so the operator should look in the local copies, not the example templates.

## 7. Run The Off-Stage Data Prep

Before you run this step, make sure `.env` already contains working Snowflake credentials and connection settings.

This block:

- resets the local seed artifacts and Snowflake landing objects for a clean rerun
- drops the entire `SNOWFLAKE_DATABASE` so the rerun starts with no source tables or leftover demo schemas
- regenerates the local telco seed files
- loads the source-shaped telco data into `SNOWFLAKE_STAGE_SCHEMA`
- verifies the seed load
- reapplies and verifies the Snowflake metadata so Horizon shows table and column descriptions on the source tables

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

## Snowflake Reproducibility Rule

Step 7 now begins with an explicit destructive wipe of the full Snowflake demo database.

The demo is reproducible because:

- `task seed:reset:confirm` removes the generated seed artifacts and drops `SNOWFLAKE_DATABASE` before a rerun
- `task seed:load` truncates and reloads the landing tables each time
- `task metadata:apply` reapplies the Horizon metadata and column descriptions on the source tables each time
- the demo contracts create or replace their demo objects in `SNOWFLAKE_FLUID_SCHEMA`

## 8. Continue To One Launchpad

After you finish the shared steps on this page, continue to exactly one of these:

- [Demo Release Launchpad (Mac)](demo-release-launchpad-mac.md)
- [Demo Release Launchpad (Windows)](demo-release-launchpad-windows.md)
- [Dev Source Launchpad (Mac)](dev-source-launchpad-mac.md)
- [Dev Source Launchpad (Windows)](dev-source-launchpad-windows.md)

Then use the matching workspace:

- ready-made variants: `gitlab/telco-silver-product-demo/README.md`
- AI variants: `gitlab/telco-silver-import-demo/README.md`

## Related Docs

- [Demo Release Launchpad (Mac)](demo-release-launchpad-mac.md)
- [Demo Release Launchpad (Windows)](demo-release-launchpad-windows.md)
- [Dev Source Launchpad (Mac)](dev-source-launchpad-mac.md)
- [Dev Source Launchpad (Windows)](dev-source-launchpad-windows.md)
- [Getting Started](getting-started.md)
- [Credentials](credentials.md)
- [Command Reference](command-reference.md)
- [FLUID Versions](fluid-versions.md)
- [FLUID Gap Register](fluid-gap-register.md)

## External Links

- TestPyPI package: [data-product-forge](https://test.pypi.org/project/data-product-forge/)
- Forge docs home: [Forge Docs](https://agenticstiger.github.io/forge_docs/)
- Snowflake quickstart: [Forge Snowflake Getting Started](https://agenticstiger.github.io/forge_docs/getting-started/snowflake)
- Source repo: [forge-cli](https://github.com/Agenticstiger/forge-cli)
