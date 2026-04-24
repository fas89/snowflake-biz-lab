# Dev Source Launchpad (Windows)

Use this track when you are iterating on the sibling `forge-cli` checkout and want the lab to run against editable source.

## Before You Start

Finish [Launchpad Common](launchpad-common.md) first. This page only covers what is different for the `dev-source` runtime.

## Track Variables

```powershell
$env:FORGE_CLI_REPO = if ($env:FORGE_CLI_REPO) { $env:FORGE_CLI_REPO } else { "$env:LOCAL_REPOS_DIR\forge-cli" }
$env:FLUID_DEV_VENV = "$env:LAB_REPO\.venv.fluid-dev"
$env:FLUID_DEV_BIN = "$env:FLUID_DEV_VENV\Scripts\fluid.exe"
$env:FLUID_CLI = $env:FLUID_DEV_BIN
$env:JENKINS_INSTALL_MODE = "dev-source"
```

## Bootstrap The Editable Runtime

```powershell
py -3 -m venv $env:FLUID_DEV_VENV
& "$env:FLUID_DEV_VENV\Scripts\python.exe" -m pip install --upgrade pip
& "$env:FLUID_DEV_VENV\Scripts\python.exe" -m pip install -e "${env:FORGE_CLI_REPO}[snowflake]"
git -C $env:FORGE_CLI_REPO branch --show-current
git -C $env:FORGE_CLI_REPO status --short --branch
& $env:FLUID_DEV_BIN version
```

What this track changes:

- local `fluid` commands run from the editable sibling checkout
- generated Jenkinsfiles use `--install-mode dev-source`
- the Jenkins container imports `fluid` from the `/forge-cli-src` bind mount

## Optional Track Check

```powershell
Set-Location $env:LAB_REPO
task fluid:check:dev
```

## Next Step

Run [Variant Playbook (Windows)](variant-playbook-windows.md) with the variables above already set.

## Related Docs

- [Launchpad Common](launchpad-common.md)
- [Variant Playbook (Windows)](variant-playbook-windows.md)
- [Launchpad Recovery](launchpad-recovery.md)
- [FLUID Gap Register](fluid-gap-register.md)
