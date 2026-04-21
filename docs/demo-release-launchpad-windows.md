# Demo Release Launchpad (Windows)

Use this when you want one uninterrupted Windows path for the final audience demo.

This launchpad is meant for testing and demoing inside a safe sandbox environment. Use it when you want to exercise the released `data-product-forge` package without changing `forge-cli` source code.

All shared setup, reset, platform bring-up, data prep, credentials, and browser links live in [Launchpad Common](launchpad-common.md). The Bronze / A1 / A2 / B1 / B2 commands live in [Variant Playbook (Windows)](variant-playbook-windows.md).

> [!CAUTION]
> Use this launchpad only against a safe sandbox environment. The runbook includes destructive reset steps for local stacks and the Snowflake demo database before the source-load path is rebuilt.

## Before You Start

1. Complete steps 1 through 8 in [Launchpad Common](launchpad-common.md). For a fully reproducible rerun, use the [Clean Start First](launchpad-common.md#clean-start-first) block there.
2. Start this page only after you reach step 8 there.

## Demo-Release Variable

```powershell
$env:FLUID_DEMO_PACKAGE_SPEC = if ($env:FLUID_DEMO_PACKAGE_SPEC) { $env:FLUID_DEMO_PACKAGE_SPEC } else { "data-product-forge" }
```

## Bootstrap Release Runtime In Both Workspaces

Each workspace gets its own venv so the released `data-product-forge` is installed side-by-side with the on-stage narrative.

> [!IMPORTANT]
> This track installs the **latest `data-product-forge` release from TestPyPI** by design — **including pre-release alphas**. TestPyPI is where release candidates (like `0.8.0a1`) are published before they're promoted to stable PyPI, so staying on TestPyPI with `--pre` means the demo validates what is about to ship. Without `--pre`, `pip` would silently skip alphas and fall back to the newest stable (e.g. `0.7.10`), which is not what we want here.
>
> To pin a specific version: `$env:FLUID_DEMO_PACKAGE_SPEC = "data-product-forge==X.Y.Z"` before running the install block.
>
> To stay on stable-only releases: drop `--pre`. To switch to the stable PyPI release instead of TestPyPI: drop both `--pre` and `--index-url` — `python -m pip install $env:FLUID_DEMO_PACKAGE_SPEC`.

### Workspace A: Ready-Made Variants

```powershell
Set-Location $env:GREENFIELD_WORKSPACE
py -3 -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
# Pulls the LATEST data-product-forge from TestPyPI; PyPI is only a fallback for
# transitive deps. See the callout above if you want to pin a version or swap
# to stable PyPI.
python -m pip install --pre --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ $env:FLUID_DEMO_PACKAGE_SPEC
fluid version
```

### Workspace B: AI Variants

```powershell
Set-Location $env:EXISTING_DBT_WORKSPACE
py -3 -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
# Same latest-TestPyPI-by-design choice as Workspace A — see callout above.
python -m pip install --pre --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ $env:FLUID_DEMO_PACKAGE_SPEC
fluid version
```

## Set The Variant-Playbook Binary

The variant playbook is parameterised. With the appropriate workspace venv active, `fluid` resolves to that venv's installed binary. Set it:

```powershell
$env:FLUID_CLI = "fluid"
```

When you move between Workspace A and Workspace B variants, re-activate the matching venv so `fluid` resolves to the right install:

```powershell
# Before A1 or A2
. "$env:GREENFIELD_WORKSPACE\.venv\Scripts\Activate.ps1"

# Before B1 or B2
. "$env:EXISTING_DBT_WORKSPACE\.venv\Scripts\Activate.ps1"
```

## Run The Variants

Follow [Variant Playbook (Windows)](variant-playbook-windows.md) for Bronze, A1, A2, B1, and B2. The playbook enforces the mandatory plan verification gate and captures the validation steps for each scenario.

## Recovery Appendix

See [Launchpad Recovery](launchpad-recovery.md) for the shared recovery blocks covering stale DMM publish, Jenkinsfile not picked up, failed `fluid apply`, and full reset. Set `$env:FLUID_CLI = "fluid"` (with the appropriate workspace venv active) before running the `fluid apply` retry in this track.

## Related Docs

- [Launchpad Common](launchpad-common.md)
- [Variant Playbook (Windows)](variant-playbook-windows.md)
- [Launchpad Recovery](launchpad-recovery.md)
- [Plan Verification Checklist](plan-verification-checklist.md)
- [Scenario Validation Matrix](scenario-validation-matrix.md)
- [Jenkins SCM Handoff](jenkins-scm-handoff.md)
- [Demo Release Launchpad (Mac)](demo-release-launchpad-mac.md)
- Workspace A root: `gitlab/path-a-telco-silver-product-demo`
- Workspace B root: `gitlab/path-b-ai-telco-silver-import-demo`
