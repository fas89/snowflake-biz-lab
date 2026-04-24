# Demo Release Launchpad (Mac)

Use this when you want one uninterrupted Mac path for the final audience demo.

This launchpad is meant for testing and demoing inside a safe sandbox environment. Use it when you want to exercise the released `data-product-forge` package without changing `forge-cli` source code.

All shared setup, reset, platform bring-up, data prep, credentials, and browser links live in [Launchpad Common](launchpad-common.md). The Bronze / A1 / A2 commands live in [Variant Playbook (Mac)](variant-playbook-mac.md).

> [!CAUTION]
> Use this launchpad only against a safe sandbox environment. The runbook includes destructive reset steps for local stacks and the Snowflake demo database before the source-load path is rebuilt.

## Before You Start

1. Complete steps 1 through 8 in [Launchpad Common](launchpad-common.md). For a fully reproducible rerun, use the [Clean Start First](launchpad-common.md#clean-start-first) block there.
2. Start this page only after you reach step 8 there.

## Demo-Release Variable

```bash
export FLUID_DEMO_PACKAGE_SPEC="${FLUID_DEMO_PACKAGE_SPEC:-data-product-forge}"
```

## Bootstrap Release Runtime

Install the released `data-product-forge` package into the ready-made workspace (Workspace A).

> [!IMPORTANT]
> This track installs the **latest `data-product-forge` release from TestPyPI** by design — **including pre-release alphas**. TestPyPI is where release candidates (like `0.8.0a1`) are published before they're promoted to stable PyPI, so staying on TestPyPI with `--pre` means the demo validates what is about to ship. Without `--pre`, `pip` would silently skip alphas and fall back to the newest stable (e.g. `0.7.10`), which is not what we want here.
>
> To pin a specific version: `export FLUID_DEMO_PACKAGE_SPEC="data-product-forge==X.Y.Z"` before running the install block.
>
> To stay on stable-only releases: drop `--pre`. To switch to the stable PyPI release instead of TestPyPI: drop both `--pre` and `--index-url` — `pip install "$FLUID_DEMO_PACKAGE_SPEC"`.

```bash
cd "$GREENFIELD_WORKSPACE"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
# Pulls the LATEST data-product-forge from TestPyPI; PyPI is only a fallback for
# transitive deps. See the callout above if you want to pin a version or swap
# to stable PyPI.
pip install --pre --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ "$FLUID_DEMO_PACKAGE_SPEC"
fluid version
```

## Set The Variant-Playbook Binary

The variant playbook is parameterised. With the Workspace A venv active, `fluid` resolves to that venv's installed binary. Export it:

```bash
export FLUID_CLI=fluid
```

If a new shell loses the venv, re-activate before running Bronze / A1 / A2:

```bash
source "$GREENFIELD_WORKSPACE/.venv/bin/activate"
```

## Run The Variants

Follow [Variant Playbook (Mac)](variant-playbook-mac.md) for Bronze, A1, and A2. The playbook enforces the mandatory plan verification gate and captures the validation steps for each scenario.

## Coming Soon — AI Forge Variants (B1, B2)

Two additional scenarios are staged for a future release of this lab:

- **B1** — AI forge with external references (references existing dbt/Airflow assets)
- **B2** — AI forge with generated assets (generates dbt/Airflow assets in-workspace)

Golden contracts and workspace scaffolds are already parked under `fluid/fixtures/forge-golden/` and `fluid/fixtures/workspaces/path-b-ai-telco-silver-import-demo/` so the B1 / B2 runbooks can be turned on without re-authoring material. You may also see a `B1-subscriber360-external` pipeline auto-provisioned in Jenkins — it's staged for that future release.

## Recovery Appendix

See [Launchpad Recovery](launchpad-recovery.md) for the shared recovery blocks covering stale DMM publish, Jenkinsfile not picked up, failed `fluid apply`, and full reset. Set `FLUID_CLI=fluid` (with the Workspace A venv active) before running the `fluid apply` retry in this track.

## Related Docs

- [Launchpad Common](launchpad-common.md)
- [Variant Playbook (Mac)](variant-playbook-mac.md)
- [Launchpad Recovery](launchpad-recovery.md)
- [Plan Verification Checklist](plan-verification-checklist.md)
- [Scenario Validation Matrix](scenario-validation-matrix.md)
- [Jenkins SCM Handoff](jenkins-scm-handoff.md)
- [Demo Release Launchpad (Windows)](demo-release-launchpad-windows.md)
- Workspace A root: `gitlab/path-a-telco-silver-product-demo`
- Workspace B root: `gitlab/path-b-ai-telco-silver-import-demo` *(staged for the Coming Soon B1 / B2 scenarios)*
