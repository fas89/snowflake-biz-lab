# Dev Source Launchpad (Mac)

Use this when you want one uninterrupted Mac path for the editable `forge-cli` development flow.

This launchpad is meant for community contributors working on [`forge-cli`](https://github.com/Agentics-Rising/forge-cli). Use it when you want to change CLI behavior locally, test those source changes, and iterate before the release-demo path.

All shared setup, reset, platform bring-up, data prep, credentials, and browser links live in [Launchpad Common](launchpad-common.md). The Bronze / A1 / A2 / B1 / B2 commands live in [Variant Playbook (Mac)](variant-playbook-mac.md).

> [!CAUTION]
> This path is for contributors working on [`forge-cli`](https://github.com/Agentics-Rising/forge-cli). Expect editable local source changes, and use only disposable sandbox infrastructure because the runbook includes destructive resets for both the local demo stacks and the Snowflake demo database.

## Before You Start

1. Complete steps 1 through 8 in [Launchpad Common](launchpad-common.md). For a fully reproducible rerun, use the [Clean Start First](launchpad-common.md#clean-start-first) block there.
2. Start this page only after you reach step 8 there.

## Dev-Source Variables

```bash
export FORGE_CLI_REPO="${FORGE_CLI_REPO:-$LOCAL_REPOS_DIR/forge-cli}"
export FLUID_DEV_VENV="$LAB_REPO/.venv.fluid-dev"
export FLUID_DEV_BIN="$FLUID_DEV_VENV/bin/fluid"
```

If you use a separate `forge-cli` worktree, override `FORGE_CLI_REPO` before bootstrapping the runtime.

## Bootstrap Source Runtime

A single lab-level venv is used across both workspaces so you always run against the same editable `forge-cli` checkout.

```bash
python3 -m venv "$FLUID_DEV_VENV"
"$FLUID_DEV_VENV/bin/pip" install --upgrade pip
"$FLUID_DEV_VENV/bin/pip" install -e "$FORGE_CLI_REPO"
git -C "$FORGE_CLI_REPO" branch --show-current
git -C "$FORGE_CLI_REPO" status --short --branch
"$FLUID_DEV_BIN" version
```

## Set The Variant-Playbook Binary

The variant playbook is parameterised. Point `FLUID_CLI` at the dev-source binary — no per-workspace venv activation needed:

```bash
export FLUID_CLI="$FLUID_DEV_BIN"
```

## Contributor Scenario Map

Use the shared scenario names when you test contributor changes in `forge-cli`.

| Scenario | Intent | Root | Contract Or Target | dbt/Airflow Mode | Contributor Focus |
| --- | --- | --- | --- | --- | --- |
| Bronze | Upstream lineage anchor | `$LAB_REPO` | `fluid/contracts/telco_seed_billing/`, `.../telco_seed_party/`, `.../telco_seed_usage/` (one contract each) | No dbt/Airflow/Jenkins assets | schema, parser, publish, lineage anchor |
| A1 | External-reference silver contract | `$GREENFIELD_WORKSPACE` | `variants/A1-external-reference/contract.fluid.yaml` | referenced dbt + referenced Airflow | reference resolution, plan/apply, publish |
| A2 | Internal-reference silver contract | `$GREENFIELD_WORKSPACE` | `variants/A2-internal-reference/contract.fluid.yaml` | packaged dbt + packaged Airflow | packaging, plan/apply, publish |
| B1 | AI forge with external references | `$EXISTING_DBT_WORKSPACE` | `variants/B1-ai-reference-external/subscriber360-external` | referenced dbt + referenced Airflow | forge interview, reference resolution |
| B2 | AI forge with generated assets | `$EXISTING_DBT_WORKSPACE` | `variants/B2-ai-generate-in-workspace/subscriber360-generated` | generated dbt + generated Airflow | generation, transformation generation, schedule generation |

Use [Scenario Validation Matrix](scenario-validation-matrix.md) for the exact contract paths, dbt roots, DAG paths, DAG IDs, Jenkinsfile paths, and expose names.

## Run The Variants

Follow [Variant Playbook (Mac)](variant-playbook-mac.md) for Bronze, A1, A2, B1, and B2. The playbook enforces the mandatory plan verification gate and captures the validation steps for each scenario. Skip the "Demo-release only" venv-activation callouts in the playbook — your single `$FLUID_DEV_BIN` already covers every variant.

## Recovery Appendix

See [Launchpad Recovery](launchpad-recovery.md) for the shared recovery blocks covering stale DMM publish, Jenkinsfile not picked up, failed `fluid apply`, and full reset. Set `FLUID_CLI="$FLUID_DEV_BIN"` before running the `fluid apply` retry in this track.

## Related Docs

- [Launchpad Common](launchpad-common.md)
- [Variant Playbook (Mac)](variant-playbook-mac.md)
- [Launchpad Recovery](launchpad-recovery.md)
- [Plan Verification Checklist](plan-verification-checklist.md)
- [Scenario Validation Matrix](scenario-validation-matrix.md)
- [Jenkins SCM Handoff](jenkins-scm-handoff.md)
- [Dev Source Launchpad (Windows)](dev-source-launchpad-windows.md)
- Workspace A root: `gitlab/path-a-telco-silver-product-demo`
- Workspace B root: `gitlab/path-b-ai-telco-silver-import-demo`
