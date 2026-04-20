"""Print the first build id from a FLUID contract YAML.

The launchpad uses this after `fluid forge` generates a contract whose
`builds[].id` is only known at runtime. It replaces the inline heredoc
parser that previously lived in the dev-source and demo-release launchpads.

Usage:
    python3 scripts/get_first_build_id.py <contract.fluid.yaml>

The script exits with a non-zero status and writes to stderr if the
contract does not exist or has no `builds:` entries. That makes it safe
to use in a shell pipeline (e.g. `BUILD_ID="$(python3 ... )"`).
"""
from __future__ import annotations

import sys
from pathlib import Path


def first_build_id(contract_path: Path) -> str | None:
    in_builds = False
    for raw in contract_path.read_text().splitlines():
        stripped = raw.strip()
        if stripped == "builds:":
            in_builds = True
            continue
        if in_builds and (stripped.startswith("- id:") or stripped.startswith("id:")):
            return stripped.split(":", 1)[1].strip()
    return None


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: get_first_build_id.py <contract.fluid.yaml>", file=sys.stderr)
        return 2
    contract = Path(sys.argv[1])
    if not contract.exists():
        print(f"Contract not found: {contract}", file=sys.stderr)
        return 1
    build_id = first_build_id(contract)
    if build_id is None:
        print(f"No builds[] entry found in {contract}", file=sys.stderr)
        return 1
    print(build_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
