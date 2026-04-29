# Variant Playbook (Windows)

Shared Bronze, A1, A2, B1, and B2 commands for Windows. Your chosen track launchpad must already have set `$env:FLUID_CLI`, `$env:FLUID_SECRETS_FILE`, and `$env:JENKINS_INSTALL_MODE`.

## Before You Start

Make sure all of these are true:

- [Launchpad Common](launchpad-common.md) is complete
- `$env:FLUID_CLI` points at the runtime for your chosen track
- `$env:JENKINS_INSTALL_MODE` is set to `dev-source` or `pypi`
- `$env:FLUID_SECRETS_FILE` points at `runtime/generated/fluid.local.env`

## Mandatory Plan Gate

Every scenario stops after `plan` until the plan review is complete:

```powershell
& $env:FLUID_CLI validate contract.fluid.yaml
& $env:FLUID_CLI plan contract.fluid.yaml --out runtime/plan.json --html
Start-Process .\runtime\plan.html
```

Review [Plan Verification Checklist](plan-verification-checklist.md) before you continue to `apply`.

## Bronze

```powershell
Set-Location $env:LAB_REPO
Get-Content $env:FLUID_SECRETS_FILE | ForEach-Object { if ($_ -match '^(?!#)([^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }

foreach ($domain in 'billing','party','usage') {
  $contract = "fluid\contracts\telco_seed_$domain\contract.fluid.yaml"
  & $env:FLUID_CLI validate $contract
  & $env:FLUID_CLI plan $contract --out "fluid\contracts\telco_seed_$domain\runtime\plan.json" --html
  & $env:FLUID_CLI publish $contract --target datamesh-manager
}
```

Validation:

- all three bronze plans review cleanly
- DMM shows `bronze.telco.billing_v1`, `bronze.telco.party_v1`, and `bronze.telco.usage_v1`
- no Jenkins jobs or Airflow DAGs are expected from Bronze

## A1 External Reference

```powershell
Set-Location "$env:GREENFIELD_WORKSPACE\variants\A1-external-reference"
Get-Content $env:FLUID_SECRETS_FILE | ForEach-Object { if ($_ -match '^(?!#)([^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
& $env:FLUID_CLI validate contract.fluid.yaml
& $env:FLUID_CLI plan contract.fluid.yaml --out runtime/plan.json --html
Start-Process .\runtime\plan.html
& $env:FLUID_CLI apply contract.fluid.yaml --mode amend-and-build --build dv2_subscriber360_reference_build --yes --report runtime/apply_report.html
& $env:FLUID_CLI generate ci contract.fluid.yaml --system jenkins --install-mode $env:JENKINS_INSTALL_MODE --default-publish-target datamesh-manager --no-verify-strict-default --publish-stage-default --no-publish-include-env --out Jenkinsfile
git status --short -- Jenkinsfile
git add Jenkinsfile
git diff --cached --quiet -- Jenkinsfile
if ($LASTEXITCODE -ne 0) {
  git commit -m "Refresh external-reference silver variant"
} else {
  Write-Host "Jenkinsfile already committed"
}
Set-Location $env:LAB_REPO
task jenkins:sync SCENARIO=A1
task jenkins:build SCENARIO=A1
Set-Location "$env:GREENFIELD_WORKSPACE\variants\A1-external-reference"
Remove-Item "$env:LAB_REPO\airflow\dags\active\current" -Recurse -Force -ErrorAction SilentlyContinue
& $env:FLUID_CLI schedule-sync --scheduler airflow --dags-dir ..\..\reference-assets\airflow_subscriber360\dags --destination "$env:LAB_REPO\airflow\dags\active\current"
& $env:FLUID_CLI publish contract.fluid.yaml --target datamesh-manager
```

Validation:

- Jenkins now lists `A1-external-reference`; it did not exist before `task jenkins:sync`
- `task jenkins:build SCENARIO=A1` runs the controller build through Jenkins `buildWithParameters` and confirms the pipeline reads `variants/A1-external-reference/Jenkinsfile`
- in the demo-release track, `task jenkins:sync` and `task jenkins:build` automatically carry the package resolved in `runtime/generated/demo-release.env`; do not add manual TestPyPI `--param` flags unless you are deliberately overriding the launchpad
- the A1 Jenkins build should succeed and publish; generate the Jenkinsfile with `--no-verify-strict-default`, `--publish-stage-default`, and `--no-publish-include-env` so the file is emitted with the lab-tuned defaults directly
- those A1 defaults are intentional because the shared Snowflake/dbt reference assets materialize nullable columns that `fluid verify --strict` would otherwise flag as constraint mismatches
- Airflow now lists DAG `telco_subscriber360_reference`; it did not exist before the `schedule-sync` command
- run `Set-Location $env:LAB_REPO; task dbt:docs:refresh SCENARIO=A1`, then confirm dbt docs shows `mart_subscriber360_core` and `mart_subscriber_health_scorecard`
- DMM shows the A1 silver product with `subscriber360_core` and `subscriber_health_scorecard`
- DMM Access agreements show A1 consuming the Bronze `party`, `usage`, and `billing` output ports
- DMM should not show duplicated Bronze SourceSystem nodes for A1, and the A1 silver product should not list product-to-product consumes as ODPS input ports

## A2 Internal Reference

```powershell
Set-Location "$env:GREENFIELD_WORKSPACE\variants\A2-internal-reference"
Get-Content $env:FLUID_SECRETS_FILE | ForEach-Object { if ($_ -match '^(?!#)([^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
& $env:FLUID_CLI validate contract.fluid.yaml
& $env:FLUID_CLI plan contract.fluid.yaml --out runtime/plan.json --html
Start-Process .\runtime\plan.html
& $env:FLUID_CLI apply contract.fluid.yaml --mode amend-and-build --build dv2_subscriber360_internal_build --yes --report runtime/apply_report.html
& $env:FLUID_CLI generate ci contract.fluid.yaml --system jenkins --install-mode $env:JENKINS_INSTALL_MODE --default-publish-target datamesh-manager --out Jenkinsfile
git status --short -- Jenkinsfile
git add Jenkinsfile
git diff --cached --quiet -- Jenkinsfile
if ($LASTEXITCODE -ne 0) {
  git commit -m "Refresh internal-reference silver variant"
} else {
  Write-Host "Jenkinsfile already committed"
}
Set-Location $env:LAB_REPO
task jenkins:sync SCENARIO=A2
task jenkins:build SCENARIO=A2
Set-Location "$env:GREENFIELD_WORKSPACE\variants\A2-internal-reference"
Remove-Item "$env:LAB_REPO\airflow\dags\active\current" -Recurse -Force -ErrorAction SilentlyContinue
& $env:FLUID_CLI schedule-sync --scheduler airflow --dags-dir .\airflow_subscriber360\dags --destination "$env:LAB_REPO\airflow\dags\active\current"
& $env:FLUID_CLI publish contract.fluid.yaml --target datamesh-manager
```

Validation:

- Jenkins now lists `A2-internal-reference`; it did not exist before `task jenkins:sync`
- `task jenkins:build SCENARIO=A2` runs the controller build through Jenkins `buildWithParameters` and confirms the pipeline reads `variants/A2-internal-reference/Jenkinsfile`
- in the demo-release track, `task jenkins:sync` and `task jenkins:build` automatically carry the package resolved in `runtime/generated/demo-release.env`; do not add manual TestPyPI `--param` flags unless you are deliberately overriding the launchpad
- the A2 Jenkins build should fail at stage `9 · verify` on `fluid verify ... --strict`; that failure is intentional in this lab and demonstrates the strict Snowflake contract gate on required vs nullable columns
- Airflow now lists DAG `telco_subscriber360_internal`; it did not exist before the `schedule-sync` command
- run `Set-Location $env:LAB_REPO; task dbt:docs:refresh SCENARIO=A2`, then confirm dbt docs shows `mart_subscriber360_core` and `mart_subscriber_health_scorecard`
- DMM shows the A2 silver product with `subscriber360_core` and `subscriber_health_scorecard`; that comes from the explicit local `fluid publish` command above, not from the intentionally failing Jenkins build
- DMM Access agreements show A2 consuming the Bronze `party`, `usage`, and `billing` output ports; A2 should not create duplicate Bronze SourceSystem nodes or product-to-product ODPS input ports

## B1 AI External Reference

B1 starts with a live provider-backed AI forge. The lab command stores the raw AI output and receipt under `runtime\generated\ai-forge\`, then hardens the generated contract with the stable B1 build id, Bronze lineage anchors, and external dbt reference needed for the runnable Snowflake flow.

```powershell
Set-Location $env:LAB_REPO
task b1:forge:ai FLUID_BIN="$env:FLUID_CLI" -- --provider gemini --model gemini-2.5-flash
# OpenAI equivalent when OPENAI_API_KEY is available:
# task b1:forge:ai FLUID_BIN="$env:FLUID_CLI" -- --provider openai --model gpt-4.1-mini

Set-Location "$env:EXISTING_DBT_WORKSPACE\variants\B1-ai-reference-external\subscriber360-external"
Get-Content $env:FLUID_SECRETS_FILE | ForEach-Object { if ($_ -match '^(?!#)([^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
$env:FLUID_UPSTREAM_CONTRACTS = "$env:LAB_REPO\fluid\contracts"
$env:Path = "$(Split-Path $env:FLUID_CLI);$env:Path"
Remove-Item Env:DBT_TARGET -ErrorAction SilentlyContinue
& $env:FLUID_CLI validate contract.fluid.yaml
& $env:FLUID_CLI generate transformation contract.fluid.yaml -o runtime/generated/dbt-preview --overwrite --dbt-validate
& $env:FLUID_CLI generate schedule contract.fluid.yaml --scheduler airflow -o runtime/generated/airflow --overwrite
& $env:FLUID_CLI plan contract.fluid.yaml --out runtime/plan.json --html
Start-Process .\runtime\plan.html
& $env:FLUID_CLI apply contract.fluid.yaml --mode amend-and-build --build ai_subscriber360_external_build --yes --report runtime/apply_report.html
& $env:FLUID_CLI generate ci contract.fluid.yaml --system jenkins --install-mode $env:JENKINS_INSTALL_MODE --default-publish-target datamesh-manager --no-verify-strict-default --publish-stage-default --no-publish-include-env --out Jenkinsfile
git status --short -- contract.fluid.yaml Jenkinsfile
git add contract.fluid.yaml Jenkinsfile
git diff --cached --quiet -- contract.fluid.yaml Jenkinsfile
if ($LASTEXITCODE -ne 0) {
  git commit -m "Refresh B1 AI external-reference variant"
} else {
  Write-Host "B1 Jenkinsfile already committed"
}
Set-Location $env:LAB_REPO
task jenkins:sync SCENARIO=B1
task jenkins:build SCENARIO=B1
Set-Location "$env:EXISTING_DBT_WORKSPACE\variants\B1-ai-reference-external\subscriber360-external"
Remove-Item "$env:LAB_REPO\airflow\dags\active\current" -Recurse -Force -ErrorAction SilentlyContinue
& $env:FLUID_CLI schedule-sync --scheduler airflow --dags-dir .\runtime\generated\airflow --destination "$env:LAB_REPO\airflow\dags\active\current"
& $env:FLUID_CLI publish contract.fluid.yaml --target datamesh-manager
```

Validation:

- `runtime\generated\ai-forge\summary.json` names the live AI provider/model used for the B1 contract
- the raw AI contract and receipt are preserved under `runtime\generated\ai-forge\raw\`
- Jenkins now lists `B1-ai-reference-external`; it did not exist before `task jenkins:sync`
- `task jenkins:build SCENARIO=B1` runs the Path B Pipeline-from-SCM job from `path-b-ai-telco-silver-import-demo`
- B1 uses the same non-strict verify and publish defaults as A1 so the Snowflake nullable-vs-required mismatch stays informational
- Airflow now lists DAG `silver_telco_subscriber360_ai_external_v1` from the generated schedule assets
- run `Set-Location $env:LAB_REPO; task dbt:docs:refresh SCENARIO=B1`, then confirm dbt docs shows `mart_subscriber360_core` and `mart_subscriber_health_scorecard`
- DMM shows the B1 silver product with `subscriber360_core` and `subscriber_health_scorecard`
- DMM Access agreements show B1 consuming the Bronze `party`, `usage`, and `billing` output ports

## B2 MCP Generated Assets

B2 starts with the forge-cli MCP server reading the seeded Snowflake schema. The lab command stores the raw MCP model under `runtime\generated\mcp-forge\`, writes the deterministic B2 contract, and generates dbt, Airflow, and Jenkins assets inside the product workspace.

```powershell
Set-Location $env:LAB_REPO
task b2:forge:mcp FLUID_BIN="$env:FLUID_CLI"

Set-Location "$env:EXISTING_DBT_WORKSPACE\variants\B2-ai-generate-in-workspace\subscriber360-generated"
Get-Content $env:FLUID_SECRETS_FILE | ForEach-Object { if ($_ -match '^(?!#)([^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
$env:FLUID_UPSTREAM_CONTRACTS = "$env:LAB_REPO\fluid\contracts"
$env:Path = "$(Split-Path $env:FLUID_CLI);$env:Path"
Remove-Item Env:DBT_TARGET -ErrorAction SilentlyContinue
& $env:FLUID_CLI validate contract.fluid.yaml
& $env:FLUID_CLI plan contract.fluid.yaml --out runtime/plan.json --html
Start-Process .\runtime\plan.html
& $env:FLUID_CLI apply contract.fluid.yaml --mode amend-and-build --build ai_subscriber360_generated_build --yes --report runtime/apply_report.html
git status --short -- contract.fluid.yaml Jenkinsfile generated
git add contract.fluid.yaml Jenkinsfile generated
git diff --cached --quiet -- contract.fluid.yaml Jenkinsfile generated
if ($LASTEXITCODE -ne 0) {
  git commit -m "Refresh B2 MCP generated-assets variant"
} else {
  Write-Host "B2 generated assets already committed"
}
Set-Location $env:LAB_REPO
task jenkins:sync SCENARIO=B2
task jenkins:build SCENARIO=B2
Set-Location "$env:EXISTING_DBT_WORKSPACE\variants\B2-ai-generate-in-workspace\subscriber360-generated"
Remove-Item "$env:LAB_REPO\airflow\dags\active\current" -Recurse -Force -ErrorAction SilentlyContinue
& $env:FLUID_CLI schedule-sync --scheduler airflow --dags-dir .\generated\airflow --destination "$env:LAB_REPO\airflow\dags\active\current"
& $env:FLUID_CLI publish contract.fluid.yaml --target datamesh-manager
```

Validation:

- `runtime\generated\mcp-forge\summary.json` names the MCP server, Snowflake schema, and table count used for B2
- the raw MCP contract and logical model are preserved under `runtime\generated\mcp-forge\raw\`
- generated dbt assets live under `generated\dbt\dbt_dv2_subscriber360`
- generated Airflow assets live under `generated\airflow`
- Jenkins now lists `B2-ai-generate-in-workspace`; it did not exist before `task jenkins:sync`
- `task jenkins:build SCENARIO=B2` runs the Path B Pipeline-from-SCM job from `path-b-ai-telco-silver-import-demo`
- Airflow now lists DAG `silver_telco_subscriber360_ai_generated_v1` from the generated schedule assets
- run `Set-Location $env:LAB_REPO; task dbt:docs:refresh SCENARIO=B2`, then confirm dbt docs shows `subscriber360_core` and `subscriber_health_scorecard`
- DMM shows the B2 silver product with `subscriber360_core` and `subscriber_health_scorecard`
- DMM Access agreements show B2 consuming the Bronze `party`, `usage`, and `billing` output ports

## Supporting Docs

- [Scenario Validation Matrix](scenario-validation-matrix.md)
- [Jenkins SCM Handoff](jenkins-scm-handoff.md)
- [Launchpad Recovery](launchpad-recovery.md)
