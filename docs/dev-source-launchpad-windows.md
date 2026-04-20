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

## Scenario Selector

Use the shared scenario names below when you test contributor changes in `forge-cli`.

| Scenario | Intent | Root | Contract Or Target | dbt/Airflow Mode | Contributor Focus |
| --- | --- | --- | --- | --- | --- |
| Bronze | Upstream lineage anchor | `$env:LAB_REPO` | `fluid/contracts/telco_seed_billing/`, `.../telco_seed_party/`, `.../telco_seed_usage/` (one contract each) | No dbt/Airflow/Jenkins assets | schema, parser, publish, lineage anchor |
| A1 | External-reference silver contract | `$env:GREENFIELD_WORKSPACE` | `variants/A1-external-reference/contract.fluid.yaml` | referenced dbt + referenced Airflow | reference resolution, plan/apply, publish |
| A2 | Internal-reference silver contract | `$env:GREENFIELD_WORKSPACE` | `variants/A2-internal-reference/contract.fluid.yaml` | packaged dbt + packaged Airflow | packaging, plan/apply, publish |
| B1 | AI forge with external references | `$env:EXISTING_DBT_WORKSPACE` | `variants/B1-ai-reference-external/subscriber360-external` | referenced dbt + referenced Airflow | forge interview, reference resolution |
| B2 | AI forge with generated assets | `$env:EXISTING_DBT_WORKSPACE` | `variants/B2-ai-generate-in-workspace/subscriber360-generated` | generated dbt + generated Airflow | generation, transformation generation, schedule generation |

Use [Scenario Validation Matrix](scenario-validation-matrix.md) for the exact contract paths, dbt roots, DAG paths, DAG IDs, Jenkinsfile paths, and expose names.

## Bronze Anchor Scenario

Bronze is published as **three contracts**, one per subject area: billing, party, and usage. They are the upstream lineage anchors for the silver variants.

Load Snowflake secrets once, then validate, plan, and publish each contract:

```powershell
Set-Location $env:LAB_REPO
Get-Content $env:FLUID_SECRETS_FILE | ForEach-Object { if ($_ -match '^(?!#)([^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }

foreach ($domain in 'billing','party','usage') {
  $contract = "fluid\contracts\telco_seed_$domain\contract.fluid.yaml"
  & $env:FLUID_DEV_BIN validate $contract
  & $env:FLUID_DEV_BIN plan $contract --out "fluid\contracts\telco_seed_$domain\runtime\plan.json" --html
  & $env:FLUID_DEV_BIN publish $contract --catalog datamesh-manager
}
```

Open the three plan reports to review them:

```powershell
Start-Process .\fluid\contracts\telco_seed_billing\runtime\plan.html
Start-Process .\fluid\contracts\telco_seed_party\runtime\plan.html
Start-Process .\fluid\contracts\telco_seed_usage\runtime\plan.html
```

Validation:

- review each of the three bronze plans against [Plan Verification Checklist](plan-verification-checklist.md)
- open the DMM marketplace at [http://localhost:8095](http://localhost:8095) and confirm all three data products appear under the **telco** domain:
  - `bronze.telco.billing_v1`
  - `bronze.telco.party_v1`
  - `bronze.telco.usage_v1`
- no Airflow, dbt, or Jenkins assets are expected for this scenario

## Workspace A: Ready-Made Variants

### A1 External Reference

```powershell
Set-Location "$env:GREENFIELD_WORKSPACE\\variants\\A1-external-reference"
Get-Content $env:FLUID_SECRETS_FILE | ForEach-Object { if ($_ -match '^(?!#)([^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
& $env:FLUID_DEV_BIN validate contract.fluid.yaml
& $env:FLUID_DEV_BIN plan contract.fluid.yaml --out runtime/plan.json --html
Start-Process .\runtime\plan.html
& $env:FLUID_DEV_BIN apply contract.fluid.yaml --build dv2_subscriber360_reference_build --yes --report runtime/apply_report.html
& $env:FLUID_DEV_BIN generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Refresh external-reference silver variant"
git push
& $env:FLUID_DEV_BIN publish contract.fluid.yaml --catalog datamesh-manager
```

Validation:

- open Airflow at [http://localhost:8085](http://localhost:8085) and confirm DAG `telco_subscriber360_reference`
- run `Set-Location $env:LAB_REPO; task dbt:docs:refresh SCENARIO=A1` then open [http://localhost:8086](http://localhost:8086) and confirm `mart_subscriber360_core` plus `mart_subscriber_health_scorecard`
- open Jenkins at [http://localhost:8081](http://localhost:8081), open the `A1-external-reference` pipeline, click **Build Now**, and confirm the run reads `variants/A1-external-reference/Jenkinsfile` and completes the generated stages
- open the DMM marketplace at [http://localhost:8095](http://localhost:8095) and confirm the A1 silver data product with its `subscriber360_core` and `subscriber_health_scorecard` exposes appears under the telco domain

### A2 Internal Reference

```powershell
Set-Location "$env:GREENFIELD_WORKSPACE\\variants\\A2-internal-reference"
Get-Content $env:FLUID_SECRETS_FILE | ForEach-Object { if ($_ -match '^(?!#)([^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
& $env:FLUID_DEV_BIN validate contract.fluid.yaml
& $env:FLUID_DEV_BIN plan contract.fluid.yaml --out runtime/plan.json --html
Start-Process .\runtime\plan.html
& $env:FLUID_DEV_BIN apply contract.fluid.yaml --build dv2_subscriber360_internal_build --yes --report runtime/apply_report.html
& $env:FLUID_DEV_BIN generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Refresh internal-reference silver variant"
git push
& $env:FLUID_DEV_BIN publish contract.fluid.yaml --catalog datamesh-manager
```

Validation:

- open Airflow at [http://localhost:8085](http://localhost:8085) and confirm DAG `telco_subscriber360_internal`
- run `Set-Location $env:LAB_REPO; task dbt:docs:refresh SCENARIO=A2` then open [http://localhost:8086](http://localhost:8086) and confirm `mart_subscriber360_core` plus `mart_subscriber_health_scorecard`
- open Jenkins at [http://localhost:8081](http://localhost:8081), open the `A2-internal-reference` pipeline, click **Build Now**, and confirm the run reads `variants/A2-internal-reference/Jenkinsfile` and completes the generated stages
- open the DMM marketplace at [http://localhost:8095](http://localhost:8095) and confirm the A2 silver data product with its `subscriber360_core` and `subscriber_health_scorecard` exposes appears under the telco domain

## Workspace B: AI Variants

The AI-created workspaces are expected to land here:

```text
%EXISTING_DBT_WORKSPACE%\\variants\\B1-ai-reference-external\\subscriber360-external
%EXISTING_DBT_WORKSPACE%\\variants\\B2-ai-generate-in-workspace\\subscriber360-generated
```

### B1 AI Forge + External References

There are two ways to run B1 — pick one based on who is watching.

**Demo mode (recommended for presentations):** copy the golden contract that `fluid forge` produced during an off-stage capture, so the on-stage flow is deterministic. See [`fluid/fixtures/forge-golden/README.md`](../fluid/fixtures/forge-golden/README.md) for how the golden is captured and refreshed.

**Live mode (for forge-cli contributors):** call the real LLM so you can iterate on prompts, providers, or templates.

```powershell
Set-Location "$env:EXISTING_DBT_WORKSPACE\\variants\\B1-ai-reference-external"
Get-Content $env:FLUID_SECRETS_FILE | ForEach-Object { if ($_ -match '^(?!#)([^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
Get-Content ..\..\prompts\ai-reference-external.md
& $env:FLUID_DEV_BIN init subscriber360-external --provider snowflake --yes
Set-Location .\subscriber360-external

# --- Demo mode: replay the captured golden contract (deterministic) ---
Copy-Item "$env:LAB_REPO\fluid\fixtures\forge-golden\B1-ai-reference-external\contract.fluid.yaml" .\contract.fluid.yaml -Force

# --- Live mode (alternative): uncomment to call the real LLM instead ---
# & $env:FLUID_DEV_BIN forge --provider snowflake --domain telco --target-dir .

& $env:FLUID_DEV_BIN validate contract.fluid.yaml
& $env:FLUID_DEV_BIN plan contract.fluid.yaml --out runtime/plan.json --html
Start-Process .\runtime\plan.html
$buildId = (py -3 "$env:LAB_REPO\scripts\get_first_build_id.py" contract.fluid.yaml).Trim()
& $env:FLUID_DEV_BIN apply contract.fluid.yaml --build $buildId --yes --report runtime/apply_report.html
& $env:FLUID_DEV_BIN generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Generate AI external-reference silver variant"
git push
& $env:FLUID_DEV_BIN publish contract.fluid.yaml --catalog datamesh-manager
```

Validation:

- open Airflow at [http://localhost:8085](http://localhost:8085) and confirm DAG `telco_subscriber360_reference`
- run `Set-Location $env:LAB_REPO; task dbt:docs:refresh SCENARIO=B1` then open [http://localhost:8086](http://localhost:8086) and confirm `mart_subscriber360_core` plus `mart_subscriber_health_scorecard`
- open Jenkins at [http://localhost:8081](http://localhost:8081), open the `B1-subscriber360-external` pipeline, click **Build Now**, and confirm the run reads `variants/B1-ai-reference-external/subscriber360-external/Jenkinsfile` and completes the generated stages
- open the DMM marketplace at [http://localhost:8095](http://localhost:8095) and confirm the `subscriber360_core` and `subscriber_health_scorecard` exposes appear under the silver data product

### B2 AI Forge + Generated Assets

There are two ways to run B2 — pick one based on who is watching.

**Demo mode (recommended for presentations):** copy the golden contract that `fluid forge` produced during an off-stage capture, so the on-stage flow is deterministic. If the golden folder also contains pre-generated `generated/dbt/` and `generated/airflow/` assets, the copy covers them too and the `generate transformation`/`generate schedule` lines become no-ops you can keep or remove. See [`fluid/fixtures/forge-golden/README.md`](../fluid/fixtures/forge-golden/README.md) for how the golden is captured and refreshed.

**Live mode (for forge-cli contributors):** call the real LLM so you can iterate on prompts, providers, or templates.

```powershell
Set-Location "$env:EXISTING_DBT_WORKSPACE\\variants\\B2-ai-generate-in-workspace"
Get-Content $env:FLUID_SECRETS_FILE | ForEach-Object { if ($_ -match '^(?!#)([^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
Get-Content ..\..\prompts\ai-generate-in-workspace.md
& $env:FLUID_DEV_BIN init subscriber360-generated --provider snowflake --yes
Set-Location .\subscriber360-generated

# --- Demo mode: replay the captured golden contract (deterministic) ---
Copy-Item "$env:LAB_REPO\fluid\fixtures\forge-golden\B2-ai-generate-in-workspace\contract.fluid.yaml" .\contract.fluid.yaml -Force

# --- Live mode (alternative): uncomment to call the real LLM instead ---
# & $env:FLUID_DEV_BIN forge --provider snowflake --domain telco --target-dir .

& $env:FLUID_DEV_BIN validate contract.fluid.yaml
& $env:FLUID_DEV_BIN plan contract.fluid.yaml --out runtime/plan.json --html
Start-Process .\runtime\plan.html
& $env:FLUID_DEV_BIN generate transformation contract.fluid.yaml --engine dbt -o generated/dbt --overwrite
& $env:FLUID_DEV_BIN generate schedule contract.fluid.yaml --scheduler airflow -o generated/airflow --overwrite
$buildId = (py -3 "$env:LAB_REPO\scripts\get_first_build_id.py" contract.fluid.yaml).Trim()
& $env:FLUID_DEV_BIN apply contract.fluid.yaml --build $buildId --yes --report runtime/apply_report.html
& $env:FLUID_DEV_BIN generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Generate AI in-workspace silver variant"
git push
& $env:FLUID_DEV_BIN publish contract.fluid.yaml --catalog datamesh-manager
```

Validation:

- open Airflow at [http://localhost:8085](http://localhost:8085) and confirm the generated DAG from `generated/airflow` appears with an ID derived from the generated contract ID
- run `Set-Location $env:LAB_REPO; task dbt:docs:refresh SCENARIO=B2` then open [http://localhost:8086](http://localhost:8086) and confirm `mart_subscriber360_core` plus `mart_subscriber_health_scorecard`
- open Jenkins at [http://localhost:8081](http://localhost:8081); B2 is not auto-provisioned (the Jenkinsfile only exists after `fluid generate ci`) — if you want the pipeline in the UI, add a JobDSL entry to `jenkins/casc/jenkins.yaml` pointing at `variants/B2-ai-generate-in-workspace/subscriber360-generated/Jenkinsfile` and rerun `task jenkins:up`
- open the DMM marketplace at [http://localhost:8095](http://localhost:8095) and confirm the B2 silver data product with its `subscriber360_core` and `subscriber_health_scorecard` exposes appears under the telco domain

## Jenkins SCM Handoff

After each `generate ci` step:

1. commit the generated `Jenkinsfile` in the workspace repo on disk
2. open the matching pipeline in Jenkins (`A1-external-reference`, `A2-internal-reference`, `B1-subscriber360-external`) and click **Build Now**

The pipelines are auto-provisioned by `task jenkins:up` via CasC JobDSL. Their SCM source is the local workspace repo mounted read-only at `/workspace/gitlab/` — `git push` is not required.

Use [Jenkins SCM Handoff](jenkins-scm-handoff.md) for the expected script paths and job model.

## Recovery Appendix

Quick resets for the failures that happen most often on a live rehearsal. Each block is self-contained — pick the row that matches what broke.

### DMM publish succeeded but nothing appears at `http://localhost:8095`

Usually the API key in `runtime/generated/fluid.local.env` is stale or the catalog stack was never bootstrapped. Refresh both:

```powershell
Set-Location $env:LAB_REPO
task catalogs:up
task catalogs:bootstrap
# then re-run the failing `fluid publish` command
```

If the UI still shows nothing, do a clean catalog reset:

```powershell
Set-Location $env:LAB_REPO
task catalogs:reset
task catalogs:up
task catalogs:bootstrap
# then re-run every `fluid publish` from the start of your scenario
```

### Jenkins did not pick up the Jenkinsfile

The CasC pipelines read from `/workspace/gitlab/` (the workspace folder on disk, not GitLab remote). Reprovision so CasC rescans:

```powershell
Set-Location $env:LAB_REPO
task jenkins:down
task jenkins:up
```

Then reopen [http://localhost:8081](http://localhost:8081) and click **Scan Multibranch Pipeline Now** on the affected job.

### `fluid apply` failed partway through (auth, role, or adapter error)

Reload Snowflake secrets into the current shell and retry the same `apply` command — the build is idempotent for the demo-scoped schema:

```powershell
Set-Location $env:WORKSPACE_PATH_FROM_YOUR_SCENARIO
Get-Content $env:FLUID_SECRETS_FILE | ForEach-Object { if ($_ -match '^(?!#)([^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
& $env:FLUID_DEV_BIN apply contract.fluid.yaml --build $buildId --yes --report runtime/apply_report.html
```

If auth is the root cause, open `runtime/generated/fluid.local.env` and confirm the `SNOWFLAKE_*` values are current; the Docker seed tasks read `.env` instead, so the two files can drift.

### Full reset (when you need a guaranteed clean rerun)

Runs the destructive reset from [Launchpad Common](launchpad-common.md#start-clean-first) and the off-stage data prep afterwards:

```powershell
Set-Location $env:LAB_REPO
py -3 scripts/reset_demo_state.py --lab-repo $env:LAB_REPO --greenfield-workspace $env:GREENFIELD_WORKSPACE --existing-workspace $env:EXISTING_DBT_WORKSPACE
task down; task jenkins:down; task catalogs:reset
task up; task jenkins:up; task catalogs:up; task catalogs:bootstrap
task seed:reset:confirm; task seed:generate; task seed:load; task seed:verify
task metadata:apply; task metadata:verify
```

Then restart this launchpad from **Bootstrap Source Runtime**.

## Related Docs

- [Launchpad Common](launchpad-common.md)
- [Plan Verification Checklist](plan-verification-checklist.md)
- [Scenario Validation Matrix](scenario-validation-matrix.md)
- [Jenkins SCM Handoff](jenkins-scm-handoff.md)
- [Dev Source Launchpad (Mac)](dev-source-launchpad-mac.md)
- Workspace A root: `gitlab/path-a-telco-silver-product-demo`
- Workspace B root: `gitlab/path-b-ai-telco-silver-import-demo`
