# Variant Playbook (Windows)

Shared Bronze, A1, and A2 commands for Windows. Your chosen track launchpad must already have set `$env:FLUID_CLI`, `$env:FLUID_SECRETS_FILE`, and `$env:JENKINS_INSTALL_MODE`.

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
& $env:FLUID_CLI generate ci contract.fluid.yaml --system jenkins --install-mode $env:JENKINS_INSTALL_MODE --default-publish-target datamesh-manager --out Jenkinsfile
@'
from pathlib import Path
path = Path("Jenkinsfile")
text = path.read_text()
text = text.replace(
    "name: 'VERIFY_STRICT',      defaultValue: true,",
    "name: 'VERIFY_STRICT',      defaultValue: false,",
)
text = text.replace(
    "name: 'RUN_STAGE_10_PUBLISH', defaultValue: false,",
    "name: 'RUN_STAGE_10_PUBLISH', defaultValue: true,",
)
text = text.replace(
    'fluid publish "${CONTRACT:-contract.fluid.yaml}" ${TARGET_FLAGS} \\\n'
    '                         --env "${FLUID_ENV:-dev}"',
    'fluid publish "${CONTRACT:-contract.fluid.yaml}" ${TARGET_FLAGS}',
)
path.write_text(text)
'@ | python
git add Jenkinsfile
git commit -m "Refresh external-reference silver variant"
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
- the A1 Jenkins build should succeed and publish; this lab keeps `VERIFY_STRICT=false`, `RUN_STAGE_10_PUBLISH=true`, and drops the unsupported `fluid publish --env ...` flag in the A1 Jenkinsfile because the shared Snowflake/dbt reference assets materialize nullable columns that `fluid verify --strict` would otherwise flag as constraint mismatches
- Airflow now lists DAG `telco_subscriber360_reference`; it did not exist before the `schedule-sync` command
- run `Set-Location $env:LAB_REPO; task dbt:docs:refresh SCENARIO=A1`, then confirm dbt docs shows `mart_subscriber360_core` and `mart_subscriber_health_scorecard`
- DMM shows the A1 silver product with `subscriber360_core` and `subscriber_health_scorecard`

## A2 Internal Reference

```powershell
Set-Location "$env:GREENFIELD_WORKSPACE\variants\A2-internal-reference"
Get-Content $env:FLUID_SECRETS_FILE | ForEach-Object { if ($_ -match '^(?!#)([^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
& $env:FLUID_CLI validate contract.fluid.yaml
& $env:FLUID_CLI plan contract.fluid.yaml --out runtime/plan.json --html
Start-Process .\runtime\plan.html
& $env:FLUID_CLI apply contract.fluid.yaml --mode amend-and-build --build dv2_subscriber360_internal_build --yes --report runtime/apply_report.html
& $env:FLUID_CLI generate ci contract.fluid.yaml --system jenkins --install-mode $env:JENKINS_INSTALL_MODE --default-publish-target datamesh-manager --out Jenkinsfile
git add Jenkinsfile
git commit -m "Refresh internal-reference silver variant"
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
- the A2 Jenkins build should fail at stage `9 · verify` on `fluid verify ... --strict`; that failure is intentional in this lab and demonstrates the strict Snowflake contract gate on required vs nullable columns
- Airflow now lists DAG `telco_subscriber360_internal`; it did not exist before the `schedule-sync` command
- run `Set-Location $env:LAB_REPO; task dbt:docs:refresh SCENARIO=A2`, then confirm dbt docs shows `mart_subscriber360_core` and `mart_subscriber_health_scorecard`
- DMM shows the A2 silver product with `subscriber360_core` and `subscriber_health_scorecard`; that comes from the explicit local `fluid publish` command above, not from the intentionally failing Jenkins build

## Supporting Docs

- [Scenario Validation Matrix](scenario-validation-matrix.md)
- [Jenkins SCM Handoff](jenkins-scm-handoff.md)
- [Launchpad Recovery](launchpad-recovery.md)
