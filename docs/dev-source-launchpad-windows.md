# Dev Source Launchpad (Windows)

Use this when you want one uninterrupted Windows path for the editable `forge-cli` development flow.

This launchpad is meant for community contributors working on [`forge-cli`](https://github.com/Agentics-Rising/forge-cli). Use it when you want to change CLI behavior locally, test those source changes, and iterate before the release-demo path.

All shared setup, reset, platform bring-up, data prep, credentials, and browser links live in [Launchpad Common](launchpad-common.md). The Bronze / A1 / A2 commands live in [Variant Playbook (Windows)](variant-playbook-windows.md).

> [!CAUTION]
> This path is for contributors working on [`forge-cli`](https://github.com/Agentics-Rising/forge-cli). Expect editable local source changes, and use only disposable sandbox infrastructure because the runbook includes destructive resets for both the local demo stacks and the Snowflake demo database.

## Before You Start

1. Complete steps 1 through 8 in [Launchpad Common](launchpad-common.md). For a fully reproducible rerun, use the [Clean Start First](launchpad-common.md#clean-start-first) block there.
2. Start this page only after you reach step 8 there.

## Dev-Source Variables

```powershell
$env:FORGE_CLI_REPO = if ($env:FORGE_CLI_REPO) { $env:FORGE_CLI_REPO } else { "$env:LOCAL_REPOS_DIR\forge-cli" }
$env:FLUID_DEV_VENV = "$env:LAB_REPO\.venv.fluid-dev"
$env:FLUID_DEV_BIN = "$env:FLUID_DEV_VENV\Scripts\fluid.exe"
```

If you use a separate `forge-cli` worktree, override `FORGE_CLI_REPO` before bootstrapping the runtime.

## Bootstrap Source Runtime

A single lab-level venv is used across both workspaces so you always run against the same editable `forge-cli` checkout.

```powershell
py -3 -m venv $env:FLUID_DEV_VENV
& "$env:FLUID_DEV_VENV\Scripts\python.exe" -m pip install --upgrade pip
& "$env:FLUID_DEV_VENV\Scripts\python.exe" -m pip install -e $env:FORGE_CLI_REPO
git -C $env:FORGE_CLI_REPO branch --show-current
git -C $env:FORGE_CLI_REPO status --short --branch
& $env:FLUID_DEV_BIN version
```

## Set The Variant-Playbook Binary

The variant playbook is parameterised. Point `$env:FLUID_CLI` at the dev-source binary — no per-workspace venv activation needed:

```powershell
$env:FLUID_CLI = $env:FLUID_DEV_BIN
```

## Contributor Scenario Map

Use the shared scenario names when you test contributor changes in `forge-cli`.

| Scenario | Intent | Root | Contract Or Target | dbt/Airflow Mode | Contributor Focus |
| --- | --- | --- | --- | --- | --- |
| Bronze | Upstream lineage anchor | `$env:LAB_REPO` | `fluid/contracts/telco_seed_billing/`, `.../telco_seed_party/`, `.../telco_seed_usage/` (one contract each) | No dbt/Airflow/Jenkins assets | schema, parser, publish, lineage anchor |
| A1 | External-reference silver contract | `$env:GREENFIELD_WORKSPACE` | `variants/A1-external-reference/contract.fluid.yaml` | referenced dbt + referenced Airflow | reference resolution, plan/apply, publish |
| A2 | Internal-reference silver contract | `$env:GREENFIELD_WORKSPACE` | `variants/A2-internal-reference/contract.fluid.yaml` | packaged dbt + packaged Airflow | packaging, plan/apply, publish |

Use [Scenario Validation Matrix](scenario-validation-matrix.md) for the exact contract paths, dbt roots, DAG paths, DAG IDs, Jenkinsfile paths, and expose names.

The AI-forge scenarios **B1** and **B2** are staged for a future release — see the [Coming Soon](#coming-soon--ai-forge-variants-b1-b2) section below.

## 11-Stage Pipeline Commands

The dev-source `$env:FLUID_DEV_BIN` ships the full 11-stage pipeline surface. The variant playbook uses the minimum sequence (validate → plan → apply → publish), but you can run every stage locally:

| Stage | Command | Purpose |
|---|---|---|
| 1 Bundle | `& $env:FLUID_CLI bundle contract.fluid.yaml --format tgz --out runtime/bundle.tgz` | Deterministic tgz + `MANIFEST.json` (SHA-256 merkle root) |
| 2 Validate | `& $env:FLUID_CLI validate contract.fluid.yaml` or `... runtime/bundle.tgz` | Schema + extension-routed checks (sqlglot, openapi-spec-validator) |
| 3 Generate artifacts | `& $env:FLUID_CLI generate artifacts contract.fluid.yaml --out runtime/artifacts/` | ODCS + ODPS-Bitol + OPDS + schedule + policy fanout |
| 4 Validate artifacts | `& $env:FLUID_CLI validate-artifacts runtime/artifacts/` | Re-verify SHA-256 + per-format validators; OPA if `tests/policies/*.rego` exists |
| 5 Diff (drift gate) | `& $env:FLUID_CLI diff contract.fluid.yaml --exit-on-drift --env dev` | Hard-fail on drift before planning |
| 6 Plan | `& $env:FLUID_CLI plan contract.fluid.yaml --out runtime/plan.json --html` | Emits `bundleDigest` + `planDigest` |
| 7 Apply | `& $env:FLUID_CLI apply runtime/plan.json --mode amend-and-build --build <id> --env dev --yes` | Mode matrix; verifies `planDigest` before any DDL |
| 8 Policy apply | `& $env:FLUID_CLI policy-apply runtime/artifacts/policy/bindings.json --mode enforce --env dev` | GRANTs after apply, before verify |
| 9 Verify | `& $env:FLUID_CLI verify contract.fluid.yaml --strict --env dev --report runtime/verify.json` | Post-apply reconciliation |
| 10 Publish | `& $env:FLUID_CLI publish contract.fluid.yaml --target datamesh-manager --target datahub --env dev` | `--target` is repeatable; accepts `NAME:endpoint` override |
| 11 Schedule sync | `& $env:FLUID_CLI schedule-sync --scheduler airflow --dags-dir runtime/artifacts/schedule/` | Path-A DAG push (Phase-7 — mwaa/composer/astronomer/prefect/dagster) |

Destructive modes (`replace`, `replace-and-build`) require `--allow-data-loss` when `$env:FLUID_ENV != "dev"` or the target has rows. See `& $env:FLUID_CLI apply --help` for the full flag matrix.

## Run The Variants

Follow [Variant Playbook (Windows)](variant-playbook-windows.md) for Bronze, A1, and A2. The playbook enforces the mandatory plan verification gate and captures the validation steps for each scenario. Skip the "Demo-release only" venv-activation callouts in the playbook — your single `$env:FLUID_DEV_BIN` already covers every variant.

## Coming Soon — AI Forge Variants (B1, B2)

Two additional scenarios are staged for a future release of this lab:

- **B1** — AI forge with external references (references existing dbt/Airflow assets)
- **B2** — AI forge with generated assets (generates dbt/Airflow assets in-workspace)

Golden contracts and workspace scaffolds are already parked under `fluid/fixtures/forge-golden/` and `fluid/fixtures/workspaces/path-b-ai-telco-silver-import-demo/` so the B1 / B2 runbooks can be turned on without re-authoring material. Relevant forge-cli gaps (`fluid init --yes`, `fluid forge --context`, fragment-first builds) are tracked in [FLUID Gap Register](fluid-gap-register.md). You may also see a `B1-subscriber360-external` pipeline auto-provisioned in Jenkins — it's staged for that future release.

## Recovery Appendix

See [Launchpad Recovery](launchpad-recovery.md) for the shared recovery blocks covering stale DMM publish, Jenkinsfile not picked up, failed `fluid apply`, and full reset. Set `$env:FLUID_CLI = $env:FLUID_DEV_BIN` before running the `fluid apply` retry in this track.

## Related Docs

- [Launchpad Common](launchpad-common.md)
- [Variant Playbook (Windows)](variant-playbook-windows.md)
- [Launchpad Recovery](launchpad-recovery.md)
- [Plan Verification Checklist](plan-verification-checklist.md)
- [Scenario Validation Matrix](scenario-validation-matrix.md)
- [Jenkins SCM Handoff](jenkins-scm-handoff.md)
- [Dev Source Launchpad (Mac)](dev-source-launchpad-mac.md)
- Workspace A root: `gitlab/path-a-telco-silver-product-demo`
- Workspace B root: `gitlab/path-b-ai-telco-silver-import-demo` *(staged for the Coming Soon B1 / B2 scenarios)*
