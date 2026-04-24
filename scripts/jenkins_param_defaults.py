from __future__ import annotations


INSTALL_PARAM_NAMES = {
    "FLUID_PACKAGE_SPEC",
    "FLUID_PIP_INDEX_URL",
    "FLUID_PIP_EXTRA_INDEX_URL",
    "FLUID_ALLOW_PRERELEASE",
}


def jenkins_default_params(
    env: dict[str, str],
    base_params: tuple[tuple[str, str], ...],
) -> dict[str, str]:
    """Return build parameters the lab should always pass to Jenkins.

    Demo-release resolves the TestPyPI package once in the launchpad and writes
    it to ``runtime/generated/demo-release.env``. These defaults carry that
    resolved package into Jenkins so the first Pipeline-from-SCM build does not
    depend on Jenkins already knowing the Jenkinsfile ``parameters {}`` block.
    """

    params = dict(base_params)
    if (env.get("JENKINS_INSTALL_MODE") or "").strip() != "pypi":
        return params

    package_spec = (
        env.get("JENKINS_FLUID_PACKAGE_SPEC")
        or env.get("FLUID_DEMO_INSTALL_SPEC")
        or ""
    ).strip()
    if not package_spec:
        return params

    params["FLUID_PACKAGE_SPEC"] = package_spec
    params["FLUID_PIP_INDEX_URL"] = (
        env.get("JENKINS_FLUID_PIP_INDEX_URL")
        or env.get("FLUID_DEMO_PIP_INDEX_URL")
        or "https://pypi.org/simple/"
    ).strip()
    params["FLUID_PIP_EXTRA_INDEX_URL"] = (
        env.get("JENKINS_FLUID_PIP_EXTRA_INDEX_URL")
        or env.get("FLUID_DEMO_PIP_EXTRA_INDEX_URL")
        or "https://test.pypi.org/simple/"
    ).strip()
    params["FLUID_ALLOW_PRERELEASE"] = (
        env.get("JENKINS_FLUID_ALLOW_PRERELEASE")
        or env.get("FLUID_DEMO_ALLOW_PRERELEASE")
        or "false"
    ).strip().lower()
    return params


def has_install_overrides(params: dict[str, str]) -> bool:
    return any(name in params and params[name] for name in INSTALL_PARAM_NAMES)
