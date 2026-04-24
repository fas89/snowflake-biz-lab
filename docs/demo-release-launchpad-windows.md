# Demo Release Launchpad (Windows)

Use this track when you want to run the lab against the released `data-product-forge` package instead of an editable source checkout.

## Before You Start

Finish [Launchpad Common](launchpad-common.md) first. This page only covers what is different for the `demo-release` runtime.

## Track Variables

```powershell
$env:FLUID_DEMO_PACKAGE_SPEC = if ($env:FLUID_DEMO_PACKAGE_SPEC) { $env:FLUID_DEMO_PACKAGE_SPEC } else { "data-product-forge[snowflake]" }
$env:FLUID_DEMO_VENV = "$env:GREENFIELD_WORKSPACE\.venv"
$env:FLUID_CLI = "$env:FLUID_DEMO_VENV\Scripts\fluid.exe"
$env:JENKINS_INSTALL_MODE = "pypi"
$env:FLUID_DEMO_PIP_INDEX_URL = if ($env:FLUID_DEMO_PIP_INDEX_URL) { $env:FLUID_DEMO_PIP_INDEX_URL } else { "https://pypi.org/simple/" }
$env:FLUID_DEMO_PIP_EXTRA_INDEX_URL = if ($env:FLUID_DEMO_PIP_EXTRA_INDEX_URL) { $env:FLUID_DEMO_PIP_EXTRA_INDEX_URL } else { "https://test.pypi.org/simple/" }
$env:FLUID_DEMO_ALLOW_PRERELEASE = if ($env:FLUID_DEMO_ALLOW_PRERELEASE) { $env:FLUID_DEMO_ALLOW_PRERELEASE } else { "false" }
```

## Bootstrap The Released Runtime

This track intentionally resolves the latest `data-product-forge` release on TestPyPI at install time unless you pin `FLUID_DEMO_PACKAGE_SPEC`.

```powershell
Set-Location $env:GREENFIELD_WORKSPACE
py -3 -m venv $env:FLUID_DEMO_VENV
. "$env:FLUID_DEMO_VENV\Scripts\Activate.ps1"
python -m pip install --upgrade pip
if ($env:FLUID_DEMO_PACKAGE_SPEC -match '(==|>=|<=|~=|>|<)') {
  $env:FLUID_DEMO_INSTALL_SPEC = $env:FLUID_DEMO_PACKAGE_SPEC
} else {
  $latestLine = python -m pip index versions --pre --index-url https://test.pypi.org/simple/ data-product-forge | Select-Object -First 1
  $latestVersion = ([regex]::Match($latestLine, '\(([^)]+)\)')).Groups[1].Value
  $env:FLUID_DEMO_INSTALL_SPEC = "$($env:FLUID_DEMO_PACKAGE_SPEC)==$latestVersion"
}
$env:JENKINS_FLUID_PACKAGE_SPEC = $env:FLUID_DEMO_INSTALL_SPEC
$env:JENKINS_FLUID_PIP_INDEX_URL = $env:FLUID_DEMO_PIP_INDEX_URL
$env:JENKINS_FLUID_PIP_EXTRA_INDEX_URL = $env:FLUID_DEMO_PIP_EXTRA_INDEX_URL
$env:JENKINS_FLUID_ALLOW_PRERELEASE = $env:FLUID_DEMO_ALLOW_PRERELEASE
New-Item -ItemType Directory -Force -Path "$env:LAB_REPO\runtime\generated" | Out-Null
@"
JENKINS_INSTALL_MODE=pypi
FLUID_DEMO_INSTALL_SPEC=$($env:FLUID_DEMO_INSTALL_SPEC)
FLUID_DEMO_PIP_INDEX_URL=$($env:FLUID_DEMO_PIP_INDEX_URL)
FLUID_DEMO_PIP_EXTRA_INDEX_URL=$($env:FLUID_DEMO_PIP_EXTRA_INDEX_URL)
FLUID_DEMO_ALLOW_PRERELEASE=$($env:FLUID_DEMO_ALLOW_PRERELEASE)
JENKINS_FLUID_PACKAGE_SPEC=$($env:JENKINS_FLUID_PACKAGE_SPEC)
JENKINS_FLUID_PIP_INDEX_URL=$($env:JENKINS_FLUID_PIP_INDEX_URL)
JENKINS_FLUID_PIP_EXTRA_INDEX_URL=$($env:JENKINS_FLUID_PIP_EXTRA_INDEX_URL)
JENKINS_FLUID_ALLOW_PRERELEASE=$($env:JENKINS_FLUID_ALLOW_PRERELEASE)
"@ | Set-Content -Encoding UTF8 "$env:LAB_REPO\runtime\generated\demo-release.env"
python -m pip install --index-url $env:FLUID_DEMO_PIP_INDEX_URL --extra-index-url $env:FLUID_DEMO_PIP_EXTRA_INDEX_URL $env:FLUID_DEMO_INSTALL_SPEC
& $env:FLUID_CLI version
```

This keeps `data-product-forge` on the newest TestPyPI release while letting dependencies resolve from stable PyPI. It also records the same resolved package in `runtime/generated/demo-release.env`, so Jenkins uses the same release on the first build without requiring extra `task jenkins:build -- --param ...` flags.

What this track changes:

- local `fluid` commands run from the released package in Workspace A
- generated Jenkinsfiles use `--install-mode pypi`
- Jenkins installs the package at build time instead of importing from `/forge-cli-src`
- `task jenkins:sync` seeds Jenkins bootstrap parameters from `runtime/generated/demo-release.env`
- `task jenkins:build` passes those demo-release parameters automatically

## Next Step

Run [Variant Playbook (Windows)](variant-playbook-windows.md) with the variables above already set.

## Related Docs

- [Launchpad Common](launchpad-common.md)
- [Variant Playbook (Windows)](variant-playbook-windows.md)
- [Launchpad Recovery](launchpad-recovery.md)
- [FLUID Gap Register](fluid-gap-register.md)
