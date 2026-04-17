from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


SCHEMA_PATTERN = re.compile(r"^fluid-schema-(\d+\.\d+(?:\.\d+)?)\.json$")
CURRENT_RELEASE_PATTERN = re.compile(r'^\s*current_release:\s*"?(.*?)"?\s*$')


def run_git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def read_feature_release(repo: Path) -> str | None:
    features_path = repo / "fluid_build" / "features.yaml"
    if not features_path.exists():
        return None
    for line in features_path.read_text(encoding="utf-8").splitlines():
        match = CURRENT_RELEASE_PATTERN.match(line)
        if match:
            return match.group(1)
    return None


def discover_bundled_schema_versions(repo: Path) -> list[str]:
    schemas_dir = repo / "fluid_build" / "schemas"
    versions: list[str] = []
    if schemas_dir.exists():
        for path in sorted(schemas_dir.glob("fluid-schema-*.json")):
            match = SCHEMA_PATTERN.match(path.name)
            if match:
                versions.append(match.group(1))
    return versions


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the sibling forge-cli checkout is aligned with the dev-source expectations."
    )
    parser.add_argument(
        "--repo",
        default="../forge-cli",
        help="Path to the forge-cli source checkout.",
    )
    parser.add_argument(
        "--expected-schema-version",
        default="0.7.2",
        help="Expected bundled schema version that repo contracts rely on.",
    )
    parser.add_argument(
        "--expected-remote-ref",
        default="origin/main",
        help="Remote ref the dev-source track should follow.",
    )
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.exists():
        raise SystemExit(f"forge-cli repo not found at {repo}")

    try:
        head = run_git(repo, "rev-parse", "HEAD")
        branch = run_git(repo, "rev-parse", "--abbrev-ref", "HEAD")
        remote_head = run_git(repo, "rev-parse", args.expected_remote_ref)
        origin_url = run_git(repo, "remote", "get-url", "origin")
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"Could not inspect git state for {repo}: {exc}") from exc

    bundled_schemas = discover_bundled_schema_versions(repo)
    current_release = read_feature_release(repo)

    print(f"forge-cli repo       : {repo}")
    print(f"Origin URL           : {origin_url}")
    print(f"Current branch       : {branch}")
    print(f"Local HEAD           : {head}")
    print(f"{args.expected_remote_ref:20}: {remote_head}")
    print(f"Bundled schemas      : {', '.join(bundled_schemas) if bundled_schemas else 'none found'}")
    print(f"features current_rel.: {current_release or 'not found'}")
    print(f"Expected schema      : {args.expected_schema_version}")

    failures: list[str] = []
    if head != remote_head:
        failures.append(
            f"Local HEAD does not match {args.expected_remote_ref}. Use the dev-source track from remote main before relying on it."
        )
    if args.expected_schema_version not in bundled_schemas:
        failures.append(
            f"Bundled schemas do not include '{args.expected_schema_version}'."
        )

    if failures:
        print("\nCheck failed:")
        for failure in failures:
            print(f"- {failure}")
        print("\nRecommended recovery:")
        print(f"git -C {repo} checkout main")
        print(f"git -C {repo} pull --ff-only origin main")
        return 1

    print("\nDev-source checkout looks aligned.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
