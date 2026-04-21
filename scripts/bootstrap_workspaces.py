#!/usr/bin/env python3
"""Bootstrap the GitLab demo workspaces from tracked templates.

Copies ``fluid/fixtures/workspaces/*`` into ``./gitlab/*`` and initializes
a fresh git repo in each destination so Jenkins' local-file SCM can
clone them. The destination is gitignored; this script is the thing
that makes it appear on a fresh clone.

Usage:
    python3 scripts/bootstrap_workspaces.py                 # create only if missing
    python3 scripts/bootstrap_workspaces.py --force         # wipe and recreate
    python3 scripts/bootstrap_workspaces.py --dest ./gitlab # custom dest root
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def _run_git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def _git_init_and_commit(workspace: Path) -> None:
    """Initialise a fresh git repo and make an Initial commit.

    Jenkins' CasC JobDSL points at ``file:///workspace/gitlab/<name>/.git``
    and clones from it, so every bootstrapped workspace needs a committed
    HEAD. We use a local-only identity to avoid depending on the
    operator's ``git config``.
    """
    _run_git(workspace, "init", "--quiet", "--initial-branch=main")
    _run_git(workspace, "config", "user.email", "demo@snowflake-telco-lab.local")
    _run_git(workspace, "config", "user.name", "Snowflake Telco Lab")
    _run_git(workspace, "add", ".")
    _run_git(workspace, "commit", "--quiet", "-m", "Initial workspace scaffold")


def bootstrap_one(src: Path, dst: Path, force: bool) -> None:
    if dst.exists():
        if not force:
            print(f"skip: {dst} already exists (use --force to wipe)")
            return
        shutil.rmtree(dst)
        print(f"wiped: {dst}")
    shutil.copytree(src, dst)
    _git_init_and_commit(dst)
    print(f"bootstrapped: {dst}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dest",
        default="./gitlab",
        help="Destination root for the bootstrapped workspaces (default: ./gitlab)",
    )
    parser.add_argument(
        "--templates",
        default="fluid/fixtures/workspaces",
        help="Templates root inside the lab repo (default: fluid/fixtures/workspaces)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Wipe existing destination workspaces before copying.",
    )
    args = parser.parse_args()

    lab_repo = Path(__file__).resolve().parent.parent
    templates_root = (lab_repo / args.templates).resolve()
    dest_root = Path(args.dest).expanduser().resolve()

    if not templates_root.is_dir():
        print(f"error: templates dir not found: {templates_root}", file=sys.stderr)
        return 1

    dest_root.mkdir(parents=True, exist_ok=True)

    workspaces = sorted(p for p in templates_root.iterdir() if p.is_dir())
    if not workspaces:
        print(f"error: no workspace templates under {templates_root}", file=sys.stderr)
        return 1

    for src in workspaces:
        bootstrap_one(src, dest_root / src.name, args.force)

    print(f"\ndone. Workspaces are at {dest_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
