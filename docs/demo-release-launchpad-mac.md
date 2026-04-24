# Demo Release Launchpad (Mac)

Use this track when you want to run the lab against the released `data-product-forge` package instead of an editable source checkout.

## Before You Start

Finish [Launchpad Common](launchpad-common.md) first. This page only covers what is different for the `demo-release` runtime.

## Track Variables

```bash
export FLUID_DEMO_PACKAGE_SPEC="${FLUID_DEMO_PACKAGE_SPEC:-data-product-forge[snowflake]}"
export FLUID_DEMO_VENV="$GREENFIELD_WORKSPACE/.venv"
export FLUID_CLI="$FLUID_DEMO_VENV/bin/fluid"
export JENKINS_INSTALL_MODE=pypi
export FLUID_DEMO_PIP_INDEX_URL="${FLUID_DEMO_PIP_INDEX_URL:-https://pypi.org/simple/}"
export FLUID_DEMO_PIP_EXTRA_INDEX_URL="${FLUID_DEMO_PIP_EXTRA_INDEX_URL:-https://test.pypi.org/simple/}"
export FLUID_DEMO_ALLOW_PRERELEASE="${FLUID_DEMO_ALLOW_PRERELEASE:-false}"
```

## Bootstrap The Released Runtime

This track intentionally resolves the latest `data-product-forge` release on TestPyPI at install time unless you pin `FLUID_DEMO_PACKAGE_SPEC`.

```bash
cd "$GREENFIELD_WORKSPACE"
python3 -m venv "$FLUID_DEMO_VENV"
source "$FLUID_DEMO_VENV/bin/activate"
pip install --upgrade pip
if printf '%s' "$FLUID_DEMO_PACKAGE_SPEC" | grep -Eq '(==|>=|<=|~=|>|<)'; then
  export FLUID_DEMO_INSTALL_SPEC="$FLUID_DEMO_PACKAGE_SPEC"
else
  FLUID_TESTPYPI_LATEST_VERSION="$(
    python -m pip index versions --pre --index-url https://test.pypi.org/simple/ data-product-forge \
      | sed -n 's/^data-product-forge (\([^)]*\)).*/\1/p' \
      | head -n1
  )"
  export FLUID_DEMO_INSTALL_SPEC="${FLUID_DEMO_PACKAGE_SPEC}==${FLUID_TESTPYPI_LATEST_VERSION}"
fi
export JENKINS_FLUID_PACKAGE_SPEC="$FLUID_DEMO_INSTALL_SPEC"
export JENKINS_FLUID_PIP_INDEX_URL="$FLUID_DEMO_PIP_INDEX_URL"
export JENKINS_FLUID_PIP_EXTRA_INDEX_URL="$FLUID_DEMO_PIP_EXTRA_INDEX_URL"
export JENKINS_FLUID_ALLOW_PRERELEASE="$FLUID_DEMO_ALLOW_PRERELEASE"
mkdir -p "$LAB_REPO/runtime/generated"
cat > "$LAB_REPO/runtime/generated/demo-release.env" <<EOF
JENKINS_INSTALL_MODE=pypi
FLUID_DEMO_INSTALL_SPEC=$FLUID_DEMO_INSTALL_SPEC
FLUID_DEMO_PIP_INDEX_URL=$FLUID_DEMO_PIP_INDEX_URL
FLUID_DEMO_PIP_EXTRA_INDEX_URL=$FLUID_DEMO_PIP_EXTRA_INDEX_URL
FLUID_DEMO_ALLOW_PRERELEASE=$FLUID_DEMO_ALLOW_PRERELEASE
JENKINS_FLUID_PACKAGE_SPEC=$JENKINS_FLUID_PACKAGE_SPEC
JENKINS_FLUID_PIP_INDEX_URL=$JENKINS_FLUID_PIP_INDEX_URL
JENKINS_FLUID_PIP_EXTRA_INDEX_URL=$JENKINS_FLUID_PIP_EXTRA_INDEX_URL
JENKINS_FLUID_ALLOW_PRERELEASE=$JENKINS_FLUID_ALLOW_PRERELEASE
EOF
pip install --index-url "$FLUID_DEMO_PIP_INDEX_URL" --extra-index-url "$FLUID_DEMO_PIP_EXTRA_INDEX_URL" "$FLUID_DEMO_INSTALL_SPEC"
"$FLUID_CLI" version
```

This keeps `data-product-forge` on the newest TestPyPI release while letting dependencies resolve from stable PyPI. It also records the same resolved package in `runtime/generated/demo-release.env`, so Jenkins uses the same release on the first build without requiring extra `task jenkins:build -- --param ...` flags.

What this track changes:

- local `fluid` commands run from the released package in Workspace A
- generated Jenkinsfiles use `--install-mode pypi`
- Jenkins installs the package at build time instead of importing from `/forge-cli-src`
- `task jenkins:sync` seeds Jenkins bootstrap parameters from `runtime/generated/demo-release.env`
- `task jenkins:build` passes those demo-release parameters automatically

## Next Step

Run [Variant Playbook (Mac)](variant-playbook-mac.md) with the variables above already exported.

## Related Docs

- [Launchpad Common](launchpad-common.md)
- [Variant Playbook (Mac)](variant-playbook-mac.md)
- [Launchpad Recovery](launchpad-recovery.md)
- [FLUID Gap Register](fluid-gap-register.md)
