"""Reset local demo artifacts so the Snowflake telco demo can be rerun cleanly.

Cleans lab-repo ephemeral outputs (venvs, dbt target/logs, seed output, generated
fluid reports, dbt-docs site) and, by default, wipes ``./gitlab/`` and re-bootstraps
the demo workspaces from ``fluid/fixtures/workspaces/`` via ``bootstrap_workspaces.py``.

The gitlab/ workspaces live inside the lab repo (gitignored) and are regenerated
from tracked templates, so a full wipe-and-rebootstrap is the correct reset flow --
there is no user-committed state to preserve.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def remove_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()
    print(f"Removed {path}")


def clear_directory(path: Path, keep_names: set[str] | None = None) -> None:
    keep_names = keep_names or set()
    if not path.exists():
        return
    for child in path.iterdir():
        if child.name in keep_names:
            continue
        remove_path(child)


def clean_lab_repo(lab_repo: Path) -> None:
    remove_path(lab_repo / ".venv.fluid-demo")
    remove_path(lab_repo / ".venv.fluid-dev")
    remove_path(lab_repo / "dbt" / "target")
    remove_path(lab_repo / "dbt" / "logs")
    clear_directory(lab_repo / "seed" / "output")
    clear_directory(lab_repo / "fluid" / "generated", {"README.md"})
    clear_directory(lab_repo / "fluid" / "reports", {"README.md"})
    remove_path(lab_repo / "runtime" / "dbt-docs" / "site")
    remove_path(lab_repo / "runtime" / "seed_load_report.json")


def rebootstrap_workspaces(lab_repo: Path) -> None:
    gitlab_dir = lab_repo / "gitlab"
    if gitlab_dir.exists():
        try:
            shutil.rmtree(gitlab_dir)
            print(f"Removed {gitlab_dir}")
        except PermissionError:
            # Some local macOS setups keep the top-level gitlab/ directory
            # entry locked down by extended attributes even though its contents
            # are writable. Clearing the children is enough for a clean
            # rebootstrap because bootstrap_workspaces.py recreates the
            # expected repo directories underneath this root.
            clear_directory(gitlab_dir)
            print(f"Cleared contents under {gitlab_dir}")
    bootstrap = lab_repo / "scripts" / "bootstrap_workspaces.py"
    subprocess.run(
        [sys.executable, str(bootstrap), "--dest", str(gitlab_dir)],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lab-repo", required=True, help="Absolute path to the snowflake-biz-lab repo.")
    parser.add_argument(
        "--no-bootstrap-workspaces",
        action="store_true",
        help="Skip wiping/re-bootstrapping ./gitlab/ (leaves whatever is currently there).",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Required to confirm deletion under the resolved paths.",
    )
    args = parser.parse_args()

    lab_repo = Path(args.lab_repo).expanduser().resolve()

    print("This will delete demo artifacts under the following resolved paths:")
    print(f"  lab repo: {lab_repo}")
    if not args.no_bootstrap_workspaces:
        print(f"  gitlab/:  {lab_repo / 'gitlab'} (wiped + rebootstrapped from templates)")

    if not args.yes:
        print("Re-run with --yes to confirm.", file=sys.stderr)
        sys.exit(1)

    clean_lab_repo(lab_repo)

    if not args.no_bootstrap_workspaces:
        rebootstrap_workspaces(lab_repo)

    print("Local demo state reset complete.")


if __name__ == "__main__":
    main()
