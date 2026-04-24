# Dev Source Launchpad (Mac)

Use this track when you are iterating on the sibling `forge-cli` checkout and want the lab to run against editable source.

## Before You Start

Finish [Launchpad Common](launchpad-common.md) first. This page only covers what is different for the `dev-source` runtime.

## Track Variables

```bash
export FORGE_CLI_REPO="${FORGE_CLI_REPO:-$LOCAL_REPOS_DIR/forge-cli}"
export FLUID_DEV_VENV="$LAB_REPO/.venv.fluid-dev"
export FLUID_DEV_BIN="$FLUID_DEV_VENV/bin/fluid"
export FLUID_CLI="$FLUID_DEV_BIN"
export JENKINS_INSTALL_MODE=dev-source
```

## Bootstrap The Editable Runtime

```bash
python3 -m venv "$FLUID_DEV_VENV"
"$FLUID_DEV_VENV/bin/pip" install --upgrade pip
"$FLUID_DEV_VENV/bin/pip" install -e "${FORGE_CLI_REPO}[snowflake]"
git -C "$FORGE_CLI_REPO" branch --show-current
git -C "$FORGE_CLI_REPO" status --short --branch
"$FLUID_DEV_BIN" version
```

What this track changes:

- local `fluid` commands run from the editable sibling checkout
- generated Jenkinsfiles use `--install-mode dev-source`
- the Jenkins container imports `fluid` from the `/forge-cli-src` bind mount

## Optional Track Check

```bash
cd "$LAB_REPO"
task fluid:check:dev
```

## Next Step

Run [Variant Playbook (Mac)](variant-playbook-mac.md) with the variables above already exported.

## Related Docs

- [Launchpad Common](launchpad-common.md)
- [Variant Playbook (Mac)](variant-playbook-mac.md)
- [Launchpad Recovery](launchpad-recovery.md)
- [FLUID Gap Register](fluid-gap-register.md)
