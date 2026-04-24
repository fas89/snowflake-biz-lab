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
python3 scripts/reset_demo_state.py --lab-repo "$LAB_REPO" --yes
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
py -3 scripts/reset_demo_state.py --lab-repo $env:LAB_REPO --yes
task down
task jenkins:down
task catalogs:reset
```

If you run the clean-start block above, skip section 1 and continue with section 2 below.

The reset script cleans lab repo artifacts and, by default, wipes `./gitlab/` and re-bootstraps the demo workspaces from `fluid/fixtures/workspaces/`. The `source runtime/generated/launchpad.local.sh` step is what refreshes the current shell variables.

## Run This Page In Order

1. Set up your local path variables.
2. Run the one-time local setup helper.
3. Fill in the local config and secret files.
4. Start the local Docker applications.
5. Open the browser tabs.
6. Find the app credentials and login values.
7. Reset demo state and run the Snowflake seed and metadata prep.
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
$env:LOCAL_REPOS_DIR
Write-Host $env:LAB_REPO
```

These local files are gitignored, so each operator can keep personal paths without affecting the repo.

## 2. Run The One-Time Local Setup

This step prepares your local working area:

- creates local `.env` files only if they do not already exist
- bootstraps the demo GitLab workspaces into `./gitlab/` from the tracked templates under `fluid/fixtures/workspaces/`

The `./gitlab/` directory is gitignored. Re-running `task workspaces:bootstrap` is always safe; it skips directories that already exist. Use `task workspaces:reset` to wipe and recreate them from templates.

### Mac

```bash
cd "$LAB_REPO"
./scripts/setup_local_demo.sh
task workspaces:bootstrap
```

### Windows

```powershell
Set-Location $env:LAB_REPO
Copy-Item .env.example .env
Copy-Item .env.catalogs.example .env.catalogs
Copy-Item .env.jenkins.example .env.jenkins
task workspaces:bootstrap
```

## 3. Fill In Your Local Config Files

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

- `.env` contains working `SNOWFLAKE_*` values for the Docker-based `task seed:*` and `task metadata:*` commands
- `runtime/generated/fluid.local.env` contains the Snowflake secrets you want the live demo to use
- `task catalogs:bootstrap` will fill or refresh `DMM_API_KEY` for you after the catalog stack starts
- `FLUID_DEMO_GITLAB_WORKSPACE` / `FLUID_AI_GITLAB_WORKSPACE` can stay blank in `.env` — docker-compose falls back to `./gitlab/path-a-telco-silver-product-demo` / `./gitlab/path-b-ai-telco-silver-import-demo` automatically

Important:

- Step 7 will not work until valid Snowflake credentials are present in `.env`
- the Step 7 seed and metadata tasks run inside Docker, so they read Snowflake auth from `.env`, not from `runtime/generated/fluid.local.env`

## 4. Start The Local Applications

Bring up the local Docker applications before opening any of the UI links below.

`task launch` is the one-shot entrypoint — it runs `task up`, `task catalogs:up`, `task catalogs:bootstrap`, and a final `task preflight` health check (DMM API key validity, Docker bind-mount visibility, bronze catalog presence) with auto-heal where safe. Jenkins is a separate opt-in because not every scenario needs it.

This block:

- runs the one-shot `task launch` (core stack + catalog stack + Entropy bootstrap + preflight)
- starts Jenkins (auto-provisions the `A1-external-reference` and `A2-internal-reference` pipelines via CasC, each pointing at the matching Jenkinsfile in the `./gitlab/` workspaces inside the lab repo; you may also see a `B1-subscriber360-external` pipeline auto-provisioned — it is staged for a future release)
- shows the resulting container state

### Mac

```bash
cd "$LAB_REPO"
task launch
task jenkins:up
task ps
```

### Windows

```powershell
Set-Location $env:LAB_REPO
task launch
task jenkins:up
task ps
```

If a launch step fails, rerun `task preflight` on its own — it reports which check (bind-mount / DMM key / bronze catalog) is still unhealthy and auto-heals the safe ones. See [Launchpad Recovery](launchpad-recovery.md) if preflight cannot self-heal.

The legacy step-by-step form still works if you want to inspect each stage:

```bash
task up
task catalogs:up
task catalogs:bootstrap
task preflight
task jenkins:up
task ps
```

## 5. Open The Browser Tabs

- Airflow: [http://localhost:8085](http://localhost:8085)
- dbt docs: [http://localhost:8086](http://localhost:8086)
- Jenkins: [http://localhost:8081](http://localhost:8081) — the `A1-external-reference` and `A2-internal-reference` pipelines are already listed on the dashboard; no manual job creation is needed. You may also see a `B1-subscriber360-external` pipeline — it is staged for a future release
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

## 7. Reset Demo State And Seed Snowflake

Before you run this step, make sure `.env` already contains working Snowflake credentials and connection settings.

This block:

- wipes `./gitlab/` and re-bootstraps the demo workspaces from tracked templates, so A1 and A2 start from a clean state (no stale `Jenkinsfile`, forged contract, or generated dbt/airflow assets). The staged B1/B2 workspace scaffolds are re-bootstrapped too so they stay ready for the Coming Soon release
- drops the entire `SNOWFLAKE_DATABASE` so the rerun starts with no source tables or leftover demo schemas
- regenerates the local telco seed files
- loads the source-shaped telco data into `SNOWFLAKE_STAGE_SCHEMA`
- verifies the seed load
- reapplies and verifies the Snowflake metadata so Horizon shows table and column descriptions on the source tables

### Mac

```bash
cd "$LAB_REPO"
task workspaces:reset
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
task workspaces:reset
task seed:reset:confirm
task seed:generate
task seed:load
task seed:verify
task metadata:apply
task metadata:verify
```

## Reproducibility Rule

Step 7 begins with a destructive wipe of both the demo GitLab workspaces and the full Snowflake demo database.

The demo is reproducible because:

- `task workspaces:reset` re-bootstraps `./gitlab/` from `fluid/fixtures/workspaces/` so no stale `Jenkinsfile`, forged contract, or generated dbt/airflow assets linger between rehearsals
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

- ready-made variants (A1, A2): `gitlab/path-a-telco-silver-product-demo/README.md`
- AI variants (B1, B2): `gitlab/path-b-ai-telco-silver-import-demo/README.md` *(staged for a future release — see Coming Soon in the launchpads)*

## Related Docs

- [Demo Release Launchpad (Mac)](demo-release-launchpad-mac.md)
- [Demo Release Launchpad (Windows)](demo-release-launchpad-windows.md)
- [Dev Source Launchpad (Mac)](dev-source-launchpad-mac.md)
- [Dev Source Launchpad (Windows)](dev-source-launchpad-windows.md)
- [Variant Playbook (Mac)](variant-playbook-mac.md)
- [Variant Playbook (Windows)](variant-playbook-windows.md)
- [Launchpad Recovery](launchpad-recovery.md)
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
