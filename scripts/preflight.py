"""Preflight health checks for the snowflake-biz-lab stack.

Invoked by ``task preflight`` (and transitively by ``task launch``) to catch the
two most common first-run speedbumps *before* they surface as confusing
``fluid`` errors downstream:

1. **DMM_API_KEY missing or stale**
   ``fluid publish`` hits Entropy's ``/api/teams`` with ``x-api-key``. When the
   key is missing or invalid, Entropy returns 403 and the CLI renders it as
   ``❌ Catalog health check failed - endpoint not accessible``, which sounds
   like a network issue. This check validates the key and re-runs
   ``bootstrap_entropy_local.py`` when it doesn't.

2. **Docker Desktop bind-mount drift (macOS fakeowner)**
   After a long-running ``task up``, Docker Desktop on macOS sometimes loses
   visibility into host-side changes made after container start, leaving
   ``/workspace/greenfield/`` empty inside ``dbt-runner`` and ``airflow-*``
   even though the host path is populated. Symptom is
   ``dbt: Invalid value for '--project-dir': Path '...' does not exist`` on
   ``task dbt:docs:refresh``. Restarting the affected services rebinds cleanly.

Both checks are idempotent and auto-healing. Exit codes:
  0 — all checks pass (healed where needed)
  1 — unrecoverable; operator must intervene (message explains what)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path
from urllib import error, request

# Re-use the shared env-file parser from the existing bootstrap scripts.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from local_env_utils import parse_env_file  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_FLUID_SECRETS = REPO_ROOT / "runtime" / "generated" / "fluid.local.env"
DEFAULT_CATALOG_ENV = REPO_ROOT / ".env.catalogs"
DEFAULT_DMM_URL = "http://localhost:8095"

DBT_RUNNER_CONTAINER = "snowflake-telco-dbt-runner"
AIRFLOW_WEB_CONTAINER = "snowflake-telco-airflow-web"
AIRFLOW_SCHED_CONTAINER = "snowflake-telco-airflow-scheduler"

# Sentinel path that exists inside the dbt-runner container only when the
# ``/workspace/greenfield`` bind-mount is alive and visible. Chosen because
# this is the first path that breaks when macOS fakeowner drift happens.
GREENFIELD_SENTINEL = "/workspace/greenfield/reference-assets"

COMPOSE_FILE = REPO_ROOT / "deploy" / "docker" / "docker-compose.yml"
COMPOSE_ENV_FILE = REPO_ROOT / ".env"

BOOTSTRAP_ENTROPY_SCRIPT = REPO_ROOT / "scripts" / "bootstrap_entropy_local.py"

# Bronze contract IDs that A1 / A2 silver products reference via inputPorts.
# If these are missing from DMM, silver publish still succeeds but the product's
# input-port lineage renders as unresolved in the DMM UI (contractId points at a
# contract that doesn't exist). Informational only — `task publish:bronze` fixes it.
BRONZE_CONTRACT_IDS = (
    "bronze.telco.party_v1",
    "bronze.telco.usage_v1",
    "bronze.telco.billing_v1",
)


def _emit(ok: bool, msg: str) -> None:
    print(f"{'OK ' if ok else 'FAIL'} {msg}")


def _run(cmd: list[str]) -> tuple[int, str]:
    """Run a subprocess quietly and return (returncode, combined_output)."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, (result.stdout + result.stderr).strip()


# -----------------------------------------------------------------------------
# Check 1: Entropy reachability (prerequisite for the DMM key check)
# -----------------------------------------------------------------------------
def check_entropy_reachable(dmm_url: str, *, timeout: float = 3.0) -> bool:
    url = f"{dmm_url.rstrip('/')}/actuator/health"
    try:
        with request.urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
    except (error.URLError, error.HTTPError, OSError):
        return False


# -----------------------------------------------------------------------------
# Check 2: DMM_API_KEY present and valid
# -----------------------------------------------------------------------------
def _validate_dmm_key(dmm_url: str, api_key: str, *, timeout: float = 5.0) -> bool:
    if not api_key:
        return False
    req = request.Request(
        f"{dmm_url.rstrip('/')}/api/teams",
        headers={"x-api-key": api_key},
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except (error.URLError, error.HTTPError, OSError):
        return False


def check_dmm_key(
    secrets_file: Path,
    catalog_env_file: Path,
    dmm_url: str,
) -> bool:
    """Validate ``DMM_API_KEY`` and re-bootstrap if missing/stale."""
    if not check_entropy_reachable(dmm_url):
        _emit(False, f"Entropy not reachable at {dmm_url} — run `task catalogs:up` first")
        return False

    secrets = parse_env_file(secrets_file)
    api_key = secrets.get("DMM_API_KEY", "").strip()
    configured_url = secrets.get("DMM_API_URL", dmm_url).strip() or dmm_url

    if _validate_dmm_key(configured_url, api_key):
        _emit(True, f"DMM_API_KEY valid against {configured_url}")
        return True

    if api_key:
        print(f"     DMM_API_KEY present in {secrets_file.name} but Entropy rejected it — re-bootstrapping")
    else:
        print(f"     DMM_API_KEY missing from {secrets_file.name} — bootstrapping")

    rc, out = _run([
        sys.executable,
        str(BOOTSTRAP_ENTROPY_SCRIPT),
        "--catalog-env-file", str(catalog_env_file),
        "--fluid-secrets-file", str(secrets_file),
    ])
    if rc != 0:
        print(out)
        _emit(False, "Entropy bootstrap failed (see output above)")
        return False

    # Re-read after bootstrap wrote the new key.
    secrets = parse_env_file(secrets_file)
    api_key = secrets.get("DMM_API_KEY", "").strip()
    if _validate_dmm_key(configured_url, api_key):
        _emit(True, "DMM_API_KEY refreshed and validated")
        return True

    _emit(False, "DMM_API_KEY still invalid after bootstrap — investigate manually")
    return False


# -----------------------------------------------------------------------------
# Check 3: Bronze products present in DMM (informational)
# -----------------------------------------------------------------------------
# Note on naming: A1 / A2 silver contracts reference bronze via
# ``inputPorts[].contractId: bronze.telco.<domain>_v1``. Those IDs exist in
# DMM as *products* (``/api/dataproducts/<id>``), not as contracts —
# ``fluid publish`` emits one data product per FLUID contract plus one ODCS
# contract per ``expose:`` (i.e. ``bronze.telco.party_v1.account_source``).
# So the right health check for "is A1's inputPort lineage target known to
# DMM?" is to hit the data-products endpoint, not the data-contracts one.
def check_bronze_products_in_dmm(dmm_url: str, api_key: str) -> bool:
    """Warn when A1/A2 input-port references are not in DMM.

    Informational only — returns True regardless. Silver publish succeeds without
    bronze in DMM; this tells operators the input-port lineage will render as
    unresolved until they run ``task publish:bronze``.
    """
    if not api_key:
        return True  # handled by check_dmm_key

    missing: list[str] = []
    for product_id in BRONZE_CONTRACT_IDS:
        req = request.Request(
            f"{dmm_url.rstrip('/')}/api/dataproducts/{product_id}",
            headers={"x-api-key": api_key},
        )
        try:
            with request.urlopen(req, timeout=5) as resp:
                if resp.status != 200:
                    missing.append(product_id)
        except error.HTTPError as exc:
            if exc.code == 404:
                missing.append(product_id)
            else:
                # Treat non-404 errors as unknown; skip the check rather than
                # false-positive warn.
                return True
        except (error.URLError, OSError):
            return True

    if not missing:
        _emit(
            True,
            f"Bronze products present in DMM ({len(BRONZE_CONTRACT_IDS)} of {len(BRONZE_CONTRACT_IDS)})",
        )
        return True

    print(f"INFO Bronze products missing from DMM: {', '.join(missing)}")
    print("     Silver publish still succeeds, but A1/A2 input-port lineage will render")
    print("     as unresolved in the DMM UI. Run `task publish:bronze` to fix.")
    return True


# -----------------------------------------------------------------------------
# Check 4: Docker bind-mount drift (macOS fakeowner)
# -----------------------------------------------------------------------------
def _container_running(name: str) -> bool:
    rc, out = _run(["docker", "inspect", "--format", "{{.State.Running}}", name])
    return rc == 0 and out.strip() == "true"


def check_bind_mounts(*, settle_seconds: float = 5.0) -> bool:
    if not _container_running(DBT_RUNNER_CONTAINER):
        _emit(False, f"{DBT_RUNNER_CONTAINER} is not running — start the core stack with `task up`")
        return False

    rc, _ = _run(["docker", "exec", DBT_RUNNER_CONTAINER, "test", "-d", GREENFIELD_SENTINEL])
    if rc == 0:
        _emit(True, f"Bind-mount healthy ({DBT_RUNNER_CONTAINER}:{GREENFIELD_SENTINEL})")
        return True

    print(f"     {GREENFIELD_SENTINEL} not visible inside {DBT_RUNNER_CONTAINER}; restarting dbt-runner + airflow")

    rc, out = _run([
        "docker", "compose",
        "-f", str(COMPOSE_FILE),
        "--env-file", str(COMPOSE_ENV_FILE),
        "restart",
        "dbt-runner", "airflow-webserver", "airflow-scheduler",
    ])
    if rc != 0:
        print(out)
        _emit(False, "docker compose restart failed")
        return False

    time.sleep(settle_seconds)
    rc, _ = _run(["docker", "exec", DBT_RUNNER_CONTAINER, "test", "-d", GREENFIELD_SENTINEL])
    if rc == 0:
        _emit(True, "Bind-mount healthy after restart")
        return True

    host_path = "./gitlab/path-a-telco-silver-product-demo/reference-assets"
    _emit(
        False,
        f"Bind-mount still empty after restart — confirm {host_path} exists on the host "
        f"(run `task workspaces:bootstrap` if it doesn't)",
    )
    return False


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight health checks for the lab stack.")
    parser.add_argument("--fluid-secrets-file", default=str(DEFAULT_FLUID_SECRETS))
    parser.add_argument("--catalog-env-file", default=str(DEFAULT_CATALOG_ENV))
    parser.add_argument("--dmm-url", default=DEFAULT_DMM_URL)
    parser.add_argument("--skip-dmm", action="store_true", help="Skip the DMM API key check")
    parser.add_argument("--skip-mounts", action="store_true", help="Skip the bind-mount check")
    parser.add_argument(
        "--skip-bronze",
        action="store_true",
        help="Skip the informational bronze-contract presence check",
    )
    args = parser.parse_args()

    print("Lab preflight")
    print("-" * 40)

    results: list[bool] = []

    if not args.skip_mounts:
        results.append(check_bind_mounts())
    if not args.skip_dmm:
        dmm_ok = check_dmm_key(
            Path(args.fluid_secrets_file),
            Path(args.catalog_env_file),
            args.dmm_url,
        )
        results.append(dmm_ok)
        # Bronze presence is informational; only useful when the key works.
        if dmm_ok and not args.skip_bronze:
            secrets = parse_env_file(Path(args.fluid_secrets_file))
            api_key = secrets.get("DMM_API_KEY", "").strip()
            configured_url = secrets.get("DMM_API_URL", args.dmm_url).strip() or args.dmm_url
            check_bronze_products_in_dmm(configured_url, api_key)

    print("-" * 40)
    if all(results):
        print("All preflight checks passed. Ready to run fluid.")
        return 0
    print("Preflight found issues. See messages above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
