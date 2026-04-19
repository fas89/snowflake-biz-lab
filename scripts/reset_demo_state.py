from __future__ import annotations

import argparse
import shutil
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
    remove_path(lab_repo / "runtime" / "seed_load_report.json")


def clean_greenfield_workspace(workspace: Path) -> None:
    remove_path(workspace / ".venv")
    remove_path(workspace / "telco-silver-product")


def clean_existing_dbt_workspace(workspace: Path) -> None:
    remove_path(workspace / ".venv")
    remove_path(workspace / "dbt")
    remove_path(workspace / "config")
    remove_path(workspace / "generated")
    remove_path(workspace / "runtime")
    remove_path(workspace / "Jenkinsfile")
    remove_path(workspace / "contract.fluid.yaml")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove local demo artifacts so the Snowflake telco demo can be rerun from a clean start."
    )
    parser.add_argument("--lab-repo", required=True, help="Absolute path to the snowflake-biz-lab repo.")
    parser.add_argument(
        "--greenfield-workspace",
        help="Absolute path to the GitLab workspace used for the greenfield demo.",
    )
    parser.add_argument(
        "--existing-workspace",
        help="Absolute path to the GitLab workspace used for the existing-dbt demo.",
    )
    args = parser.parse_args()

    lab_repo = Path(args.lab_repo).expanduser().resolve()
    clean_lab_repo(lab_repo)

    if args.greenfield_workspace:
        clean_greenfield_workspace(Path(args.greenfield_workspace).expanduser().resolve())

    if args.existing_workspace:
        clean_existing_dbt_workspace(Path(args.existing_workspace).expanduser().resolve())

    print("Local demo state reset complete.")


if __name__ == "__main__":
    main()
