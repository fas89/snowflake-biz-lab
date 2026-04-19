# Dev Source Launchpad (Windows)

Use this when you want one uninterrupted Windows path for the editable `forge-cli` development flow.

This launchpad is meant for community contributors working on [`forge-cli`](https://github.com/Agentics-Rising/forge-cli). Use it when you want to change CLI behavior locally, test those source changes, and iterate before the release-demo path.

All shared setup, reset, platform bring-up, data prep, credentials, and browser links live in [Launchpad Common](launchpad-common.md).

> [!CAUTION]
> This path is for contributors working on [`forge-cli`](https://github.com/Agentics-Rising/forge-cli). Expect editable local source changes, and use only disposable sandbox infrastructure because the runbook includes destructive resets for both the local demo stacks and the Snowflake demo database.

## Start Clean First

If you want a fully reproducible rerun, start with the shared reset flow before anything else:

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

Then return to [Launchpad Common](launchpad-common.md) and continue from step 2.

## Before You Start

1. Complete steps 1 through 8 in [Launchpad Common](launchpad-common.md).
2. Start this page only after you reach step 8 there.

## Dev-Source Variables

```powershell
$env:FORGE_CLI_REPO = if ($env:FORGE_CLI_REPO) { $env:FORGE_CLI_REPO } else { "$env:LOCAL_REPOS_DIR\\forge-cli" }
$env:FLUID_DEV_VENV = "$env:LAB_REPO\\.venv.fluid-dev"
$env:FLUID_DEV_BIN = "$env:FLUID_DEV_VENV\\Scripts\\fluid.exe"
```

If you use a separate `forge-cli` worktree, override `FORGE_CLI_REPO` before bootstrapping the runtime.

## Bootstrap Source Runtime

```powershell
py -3 -m venv $env:FLUID_DEV_VENV
& "$env:FLUID_DEV_VENV\\Scripts\\python.exe" -m pip install --upgrade pip
& "$env:FLUID_DEV_VENV\\Scripts\\python.exe" -m pip install -e $env:FORGE_CLI_REPO
git -C $env:FORGE_CLI_REPO branch --show-current
git -C $env:FORGE_CLI_REPO status --short --branch
& $env:FLUID_DEV_BIN version
```

## Mandatory Plan Verification Gate

Every variant in both workspaces must stop after `plan`.

Use this exact gate:

```powershell
& $env:FLUID_DEV_BIN validate contract.fluid.yaml
& $env:FLUID_DEV_BIN plan contract.fluid.yaml --out runtime/plan.json --html
Start-Process .\runtime\plan.html
```

Then review:

- [Plan Verification Checklist](plan-verification-checklist.md)

Do not run `& $env:FLUID_DEV_BIN apply ... --build` until the checklist is complete and the plan is confirmed.

## Workspace A: Ready-Made Variants

### A1 External Reference

```powershell
Set-Location "$env:GREENFIELD_WORKSPACE\\variants\\external-reference"
Get-Content $env:FLUID_SECRETS_FILE | ForEach-Object { if ($_ -match '^(?!#)([^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
& $env:FLUID_DEV_BIN validate contract.fluid.yaml
& $env:FLUID_DEV_BIN plan contract.fluid.yaml --out runtime/plan.json --html
Start-Process .\runtime\plan.html
& $env:FLUID_DEV_BIN apply contract.fluid.yaml --build --yes --report runtime/apply_report.html
& $env:FLUID_DEV_BIN generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Refresh external-reference silver variant"
git push
& $env:FLUID_DEV_BIN publish contract.fluid.yaml --catalog entropy-local
```

### A2 Internal Reference

```powershell
Set-Location "$env:GREENFIELD_WORKSPACE\\variants\\internal-reference"
Get-Content $env:FLUID_SECRETS_FILE | ForEach-Object { if ($_ -match '^(?!#)([^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
& $env:FLUID_DEV_BIN validate contract.fluid.yaml
& $env:FLUID_DEV_BIN plan contract.fluid.yaml --out runtime/plan.json --html
Start-Process .\runtime\plan.html
& $env:FLUID_DEV_BIN apply contract.fluid.yaml --build --yes --report runtime/apply_report.html
& $env:FLUID_DEV_BIN generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Refresh internal-reference silver variant"
git push
& $env:FLUID_DEV_BIN publish contract.fluid.yaml --catalog entropy-local
```

## Workspace B: AI Variants

The AI-created workspaces are expected to land here:

```text
%EXISTING_DBT_WORKSPACE%\\variants\\ai-reference-external\\subscriber360-external
%EXISTING_DBT_WORKSPACE%\\variants\\ai-generate-in-workspace\\subscriber360-generated
```

### B1 AI Forge + External References

```powershell
Set-Location "$env:EXISTING_DBT_WORKSPACE\\variants\\ai-reference-external"
Get-Content $env:FLUID_SECRETS_FILE | ForEach-Object { if ($_ -match '^(?!#)([^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
Get-Content ..\..\prompts\ai-reference-external.md
& $env:FLUID_DEV_BIN init subscriber360-external --provider snowflake --yes
Set-Location .\subscriber360-external
& $env:FLUID_DEV_BIN forge --provider snowflake --domain telco --target-dir .
& $env:FLUID_DEV_BIN validate contract.fluid.yaml
& $env:FLUID_DEV_BIN plan contract.fluid.yaml --out runtime/plan.json --html
Start-Process .\runtime\plan.html
& $env:FLUID_DEV_BIN apply contract.fluid.yaml --build --yes --report runtime/apply_report.html
& $env:FLUID_DEV_BIN generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Generate AI external-reference silver variant"
git push
& $env:FLUID_DEV_BIN publish contract.fluid.yaml --catalog entropy-local
```

### B2 AI Forge + Generated Assets

```powershell
Set-Location "$env:EXISTING_DBT_WORKSPACE\\variants\\ai-generate-in-workspace"
Get-Content $env:FLUID_SECRETS_FILE | ForEach-Object { if ($_ -match '^(?!#)([^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
Get-Content ..\..\prompts\ai-generate-in-workspace.md
& $env:FLUID_DEV_BIN init subscriber360-generated --provider snowflake --yes
Set-Location .\subscriber360-generated
& $env:FLUID_DEV_BIN forge --provider snowflake --domain telco --target-dir .
& $env:FLUID_DEV_BIN validate contract.fluid.yaml
& $env:FLUID_DEV_BIN plan contract.fluid.yaml --out runtime/plan.json --html
Start-Process .\runtime\plan.html
& $env:FLUID_DEV_BIN apply contract.fluid.yaml --build --yes --report runtime/apply_report.html
& $env:FLUID_DEV_BIN generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Generate AI in-workspace silver variant"
git push
& $env:FLUID_DEV_BIN publish contract.fluid.yaml --catalog entropy-local
```

## Jenkins SCM Handoff

After each `generate ci` step:

1. commit the generated `Jenkinsfile`
2. push the workspace repo to GitLab
3. let Jenkins pick up the pipeline from SCM

Use [Jenkins SCM Handoff](jenkins-scm-handoff.md) for the expected script paths and job model.

## Related Docs

- [Launchpad Common](launchpad-common.md)
- [Plan Verification Checklist](plan-verification-checklist.md)
- [Jenkins SCM Handoff](jenkins-scm-handoff.md)
- [Dev Source Launchpad (Mac)](dev-source-launchpad-mac.md)
- Workspace A root: `gitlab/telco-silver-product-demo`
- Workspace B root: `gitlab/telco-silver-import-demo`
