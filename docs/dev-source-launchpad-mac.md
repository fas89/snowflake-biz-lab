# Dev Source Launchpad (Mac)

Use this when you want one uninterrupted Mac path for the editable `forge-cli` development flow.

This launchpad is meant for community contributors working on [`forge-cli`](https://github.com/Agentics-Rising/forge-cli). Use it when you want to change CLI behavior locally, test those source changes, and iterate before the release-demo path.

All shared setup, reset, platform bring-up, data prep, credentials, and browser links live in [Launchpad Common](launchpad-common.md).

> [!CAUTION]
> This path is for contributors working on [`forge-cli`](https://github.com/Agentics-Rising/forge-cli). Expect editable local source changes, and use only disposable sandbox infrastructure because the runbook includes destructive resets for both the local demo stacks and the Snowflake demo database.

## Start Clean First

If you want a fully reproducible rerun, start with the shared reset flow before anything else:

```bash
cd "$LAB_REPO"
./scripts/setup_mac_launchpad.sh --force
source runtime/generated/launchpad.local.sh
python3 scripts/reset_demo_state.py --lab-repo "$LAB_REPO" --greenfield-workspace "$GREENFIELD_WORKSPACE" --existing-workspace "$EXISTING_DBT_WORKSPACE"
task down
task jenkins:down
task catalogs:reset
```

Then return to [Launchpad Common](launchpad-common.md) and continue from step 2.

## Before You Start

1. Complete steps 1 through 8 in [Launchpad Common](launchpad-common.md).
2. Start this page only after you reach step 8 there.

## Dev-Source Variables

```bash
export FORGE_CLI_REPO="${FORGE_CLI_REPO:-$LOCAL_REPOS_DIR/forge-cli}"
export FLUID_DEV_VENV="$LAB_REPO/.venv.fluid-dev"
export FLUID_DEV_BIN="$FLUID_DEV_VENV/bin/fluid"
```

If you use a separate `forge-cli` worktree, override `FORGE_CLI_REPO` before bootstrapping the runtime.

## Bootstrap Source Runtime

```bash
python3 -m venv "$FLUID_DEV_VENV"
"$FLUID_DEV_VENV/bin/pip" install --upgrade pip
"$FLUID_DEV_VENV/bin/pip" install -e "$FORGE_CLI_REPO"
git -C "$FORGE_CLI_REPO" branch --show-current
git -C "$FORGE_CLI_REPO" status --short --branch
"$FLUID_DEV_BIN" version
```

## Mandatory Plan Verification Gate

Every variant in both workspaces must stop after `plan`.

Use this exact gate:

```bash
"$FLUID_DEV_BIN" validate contract.fluid.yaml
"$FLUID_DEV_BIN" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
```

Then review:

- [Plan Verification Checklist](plan-verification-checklist.md)

Do not run `"$FLUID_DEV_BIN" apply ... --build` until the checklist is complete and the plan is confirmed.

## Workspace A: Ready-Made Variants

### A1 External Reference

```bash
cd "$GREENFIELD_WORKSPACE/variants/external-reference"
set -a
source "$FLUID_SECRETS_FILE"
set +a
"$FLUID_DEV_BIN" validate contract.fluid.yaml
"$FLUID_DEV_BIN" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
"$FLUID_DEV_BIN" apply contract.fluid.yaml --build --yes --report runtime/apply_report.html
"$FLUID_DEV_BIN" generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Refresh external-reference silver variant"
git push
"$FLUID_DEV_BIN" publish contract.fluid.yaml --catalog entropy-local
```

### A2 Internal Reference

```bash
cd "$GREENFIELD_WORKSPACE/variants/internal-reference"
set -a
source "$FLUID_SECRETS_FILE"
set +a
"$FLUID_DEV_BIN" validate contract.fluid.yaml
"$FLUID_DEV_BIN" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
"$FLUID_DEV_BIN" apply contract.fluid.yaml --build --yes --report runtime/apply_report.html
"$FLUID_DEV_BIN" generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Refresh internal-reference silver variant"
git push
"$FLUID_DEV_BIN" publish contract.fluid.yaml --catalog entropy-local
```

## Workspace B: AI Variants

The AI-created workspaces are expected to land here:

```text
$EXISTING_DBT_WORKSPACE/variants/ai-reference-external/subscriber360-external
$EXISTING_DBT_WORKSPACE/variants/ai-generate-in-workspace/subscriber360-generated
```

### B1 AI Forge + External References

```bash
cd "$EXISTING_DBT_WORKSPACE/variants/ai-reference-external"
set -a
source "$FLUID_SECRETS_FILE"
set +a
cat ../../prompts/ai-reference-external.md
"$FLUID_DEV_BIN" init subscriber360-external --provider snowflake --yes
cd subscriber360-external
"$FLUID_DEV_BIN" forge --provider snowflake --domain telco --target-dir .
"$FLUID_DEV_BIN" validate contract.fluid.yaml
"$FLUID_DEV_BIN" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
"$FLUID_DEV_BIN" apply contract.fluid.yaml --build --yes --report runtime/apply_report.html
"$FLUID_DEV_BIN" generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Generate AI external-reference silver variant"
git push
"$FLUID_DEV_BIN" publish contract.fluid.yaml --catalog entropy-local
```

### B2 AI Forge + Generated Assets

```bash
cd "$EXISTING_DBT_WORKSPACE/variants/ai-generate-in-workspace"
set -a
source "$FLUID_SECRETS_FILE"
set +a
cat ../../prompts/ai-generate-in-workspace.md
"$FLUID_DEV_BIN" init subscriber360-generated --provider snowflake --yes
cd subscriber360-generated
"$FLUID_DEV_BIN" forge --provider snowflake --domain telco --target-dir .
"$FLUID_DEV_BIN" validate contract.fluid.yaml
"$FLUID_DEV_BIN" plan contract.fluid.yaml --out runtime/plan.json --html
open runtime/plan.html
"$FLUID_DEV_BIN" apply contract.fluid.yaml --build --yes --report runtime/apply_report.html
"$FLUID_DEV_BIN" generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Generate AI in-workspace silver variant"
git push
"$FLUID_DEV_BIN" publish contract.fluid.yaml --catalog entropy-local
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
- [Dev Source Launchpad (Windows)](dev-source-launchpad-windows.md)
- Workspace A root: `gitlab/telco-silver-product-demo`
- Workspace B root: `gitlab/telco-silver-import-demo`
