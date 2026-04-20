# Windows Greenfield Demo

This is the Windows parallel to the Mac greenfield runbook.

It keeps the same story and checkpoints, but all commands are written for PowerShell so the platform flow stays separate from the Mac version.

## Standard Shell Variables

```powershell
$env:LAB_REPO = "C:\Users\<you>\Documents\Open-Source Community\snowflake-biz-lab"
$env:GREENFIELD_WORKSPACE = "$HOME\gitlab\path-a-telco-silver-product-demo"
$env:FLUID_SECRETS_FILE = "$env:LAB_REPO\runtime\generated\fluid.local.env"
```

## Step 1: Bring Up The Local Platform

```powershell
Set-Location $env:LAB_REPO
task up
task jenkins:up
task catalogs:up
task catalogs:bootstrap
task ps
```

Checkpoint:

- Airflow opens at [http://localhost:8085](http://localhost:8085)
- dbt docs opens at [http://localhost:8086](http://localhost:8086)
- Jenkins opens at [http://localhost:8081](http://localhost:8081)
- Entropy / DMM opens at [http://localhost:8095](http://localhost:8095)
- the Entropy admin account is already usable
- `DMM_API_KEY` has been refreshed in `runtime/generated/fluid.local.env`

## Step 2: Seed Snowflake Staging

This step starts by dropping the full demo database, so only point it at disposable demo Snowflake objects.

```powershell
Set-Location $env:LAB_REPO
task seed:reset:confirm
task seed:generate
task seed:load
task seed:verify
task metadata:apply
task metadata:verify
```

Checkpoint:

- the telco landing tables exist in `SNOWFLAKE_STAGE_SCHEMA`
- Horizon metadata is applied on those source tables before FLUID starts building the silver story
- table and column descriptions are visible in Horizon without needing dbt-built schemas first

## Step 3: Install `data-product-forge` In The GitLab Workspace

```powershell
Set-Location $env:GREENFIELD_WORKSPACE
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ data-product-forge
fluid version
fluid doctor
```

Checkpoint:

- you have shown the install step live
- the room sees the released CLI, not a hidden local checkout

## Step 4: Start The FLUID Workspace

```powershell
Set-Location $env:GREENFIELD_WORKSPACE
fluid init telco-silver-product --provider snowflake --yes
Set-Location .\telco-silver-product
```

Checkpoint:

- you are now working in the GitLab path on Windows
- the demo has moved from platform prep into data-product authoring

## Step 5: Load Runtime Secrets

```powershell
Get-Content $env:FLUID_SECRETS_FILE |
  Where-Object { $_ -match '^[A-Za-z_][A-Za-z0-9_]*=' } |
  ForEach-Object {
    $name, $value = $_ -split '=', 2
    Set-Item -Path "Env:$name" -Value $value
  }
```

Checkpoint:

- you can say clearly that secrets live outside the contract

## Step 6: Forge The Silver-Layer Data Product

Run:

```powershell
fluid forge --provider snowflake --domain telco --target-dir .
```

Suggested spoken prompt for the AI step:

See [Greenfield Forge Prompt](greenfield-forge-prompt.md).

Checkpoint:

- the story is now clearly about a silver aggregated telco product
- you have shown AI-assisted contract authoring, not just a static file

## Step 7: Generate Airflow And Jenkins

```powershell
fluid generate schedule contract.fluid.yaml --scheduler airflow -o generated/airflow --overwrite
fluid generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
```

Checkpoint:

- local Airflow can now watch the generated DAG directory through the workspace bridge
- run `task dbt:docs:refresh SCENARIO=B2` from `$env:LAB_REPO` when you want the generated dbt project visible at [http://localhost:8086](http://localhost:8086)
- a `Jenkinsfile` exists in the workspace for the CI/CD part of the story

## Step 8: Validate And Plan

```powershell
fluid validate contract.fluid.yaml
fluid plan contract.fluid.yaml --out runtime/plan.json --html
Start-Process .\runtime\plan.html
```

Checkpoint:

- the plan JSON is saved in `runtime/plan.json`
- the HTML view is saved in `runtime/plan.html`
- review [Plan Verification Checklist](../../docs/plan-verification-checklist.md) before you continue
- this is the best moment to narrate what FLUID will do before you apply it

## Step 9: Apply

```powershell
$inBuilds = $false
$buildId = $null
foreach ($line in Get-Content contract.fluid.yaml) {
  $trimmed = $line.Trim()
  if ($trimmed -eq 'builds:') { $inBuilds = $true; continue }
  if ($inBuilds -and ($trimmed.StartsWith('- id:') -or $trimmed.StartsWith('id:'))) {
    $buildId = $trimmed.Split(':', 2)[1].Trim()
    break
  }
}
fluid apply contract.fluid.yaml --build $buildId --yes --report runtime/apply_report.html
```

Checkpoint:

- the data product deployment step has run
- the apply report is saved in `runtime/apply_report.html`

The generated Jenkins handoff now follows [Jenkins SCM Handoff](../../docs/jenkins-scm-handoff.md).

## Step 10: Export Standards And Publish To DMM

```powershell
fluid generate standard contract.fluid.yaml --format opds -o runtime/exports/product.opds.json
fluid generate standard contract.fluid.yaml --format odcs -o runtime/exports/product.odcs.yaml
fluid generate standard contract.fluid.yaml --format odps -o runtime/exports/product.odps.yaml
fluid publish contract.fluid.yaml --catalog datamesh-manager
```

Checkpoint:

- you end with standards artifacts plus marketplace publication
- Entropy / DMM becomes the closing product-discovery story

## Presenter Notes

- Say out loud that the demo uses the released CLI from TestPyPI.
- Say out loud that `fluidVersion` inside the contract is a separate compatibility layer.
- Keep the [FLUID Gap Register](../../docs/fluid-gap-register.md) open so you can note any release gaps you want to fix later in `forge-cli`.
