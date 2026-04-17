from __future__ import annotations

import argparse
import importlib.metadata
import re
import subprocess
import sys
from pathlib import Path


SCHEMA_PATTERN = re.compile(r"^fluid-schema-(\d+\.\d+(?:\.\d+)?)\.json$")


def parse_package_spec(package_spec: str) -> tuple[str, str | None]:
    if "==" in package_spec:
        name, version = package_spec.split("==", 1)
        return name.strip(), version.strip()
    return package_spec.strip(), None


def discover_bundled_schema_versions() -> list[str]:
    try:
        import fluid_build  # type: ignore
    except ImportError as exc:  # pragma: no cover - surfaced as a friendly CLI error
        raise RuntimeError("The installed runtime does not expose the 'fluid_build' package.") from exc

    schemas_dir = Path(fluid_build.__file__).resolve().parent / "schemas"
    versions: list[str] = []
    if schemas_dir.exists():
        for path in sorted(schemas_dir.glob("fluid-schema-*.json")):
            match = SCHEMA_PATTERN.match(path.name)
            if match:
                versions.append(match.group(1))
    return versions


def run_cli_version(fluid_bin: Path) -> str:
    completed = subprocess.run(
        [str(fluid_bin), "version", "--short"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the pinned demo-release FLUID runtime and bundled schema support."
    )
    parser.add_argument(
        "--fluid",
        default="fluid",
        help="Path to the FLUID CLI binary inside the release venv.",
    )
    parser.add_argument(
        "--expected-package-spec",
        default="data-product-forge==0.7.10",
        help="Pinned package spec that the demo-release track should match.",
    )
    parser.add_argument(
        "--expected-schema-version",
        default="0.7.2",
        help="Expected contract schema version to find in bundled schemas.",
    )
    args = parser.parse_args()

    distribution_name, expected_version = parse_package_spec(args.expected_package_spec)

    try:
        installed_version = importlib.metadata.version(distribution_name)
    except importlib.metadata.PackageNotFoundError as exc:
        raise SystemExit(f"Package '{distribution_name}' is not installed in this runtime.") from exc

    fluid_bin = Path(args.fluid).resolve()
    if not fluid_bin.exists():
        raise SystemExit(f"Could not find FLUID CLI binary at {fluid_bin}")

    cli_version = run_cli_version(fluid_bin)
    schema_versions = discover_bundled_schema_versions()

    print(f"Demo package        : {distribution_name}")
    print(f"Installed version   : {installed_version}")
    print(f"CLI version         : {cli_version}")
    print(f"Expected pin        : {expected_version or '(unversioned spec)'}")
    print(f"Bundled schemas     : {', '.join(schema_versions) if schema_versions else 'none found'}")
    print(f"Expected contract   : {args.expected_schema_version}")

    failures: list[str] = []
    if expected_version and installed_version != expected_version:
        failures.append(
            f"Installed version '{installed_version}' does not match expected '{expected_version}'."
        )
    if cli_version != installed_version:
        failures.append(
            f"`fluid version --short` returned '{cli_version}', which does not match installed package version '{installed_version}'."
        )
    if args.expected_schema_version not in schema_versions:
        failures.append(
            f"Bundled schemas do not include '{args.expected_schema_version}'."
        )

    if failures:
        print("\nCheck failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nDemo-release runtime looks good.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
