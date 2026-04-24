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
```

## Bootstrap The Released Runtime

This track intentionally resolves the latest `data-product-forge` release on TestPyPI at install time unless you pin `FLUID_DEMO_PACKAGE_SPEC`.

```bash
cd "$GREENFIELD_WORKSPACE"
python3 -m venv "$FLUID_DEMO_VENV"
source "$FLUID_DEMO_VENV/bin/activate"
pip install --upgrade pip
if printf '%s' "$FLUID_DEMO_PACKAGE_SPEC" | grep -Eq '(==|>=|<=|~=|>|<)'; then
  FLUID_DEMO_INSTALL_SPEC="$FLUID_DEMO_PACKAGE_SPEC"
else
  FLUID_TESTPYPI_LATEST_VERSION="$(
    python -m pip index versions --pre --index-url https://test.pypi.org/simple/ data-product-forge \
      | sed -n 's/^data-product-forge (\([^)]*\)).*/\1/p' \
      | head -n1
  )"
  FLUID_DEMO_INSTALL_SPEC="${FLUID_DEMO_PACKAGE_SPEC}==${FLUID_TESTPYPI_LATEST_VERSION}"
fi
pip install --index-url https://pypi.org/simple/ --extra-index-url https://test.pypi.org/simple/ "$FLUID_DEMO_INSTALL_SPEC"
"$FLUID_CLI" version
```

This keeps `data-product-forge` on the newest TestPyPI release while letting dependencies resolve from stable PyPI.

What this track changes:

- local `fluid` commands run from the released package in Workspace A
- generated Jenkinsfiles use `--install-mode pypi`
- Jenkins installs the package at build time instead of importing from `/forge-cli-src`

## Next Step

Run [Variant Playbook (Mac)](variant-playbook-mac.md) with the variables above already exported.

## Related Docs

- [Launchpad Common](launchpad-common.md)
- [Variant Playbook (Mac)](variant-playbook-mac.md)
- [Launchpad Recovery](launchpad-recovery.md)
- [FLUID Gap Register](fluid-gap-register.md)
