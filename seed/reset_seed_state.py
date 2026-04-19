from __future__ import annotations

import argparse
import sys
from pathlib import Path

from config.snowflake_utils import execute_many, fq_name, get_connection, get_env

REPO_ROOT = Path(__file__).resolve().parents[1]


def build_reset_statements() -> list[str]:
    database = get_env("SNOWFLAKE_DATABASE", required=True)
    return [f"DROP DATABASE IF EXISTS {fq_name(database)}"]


def clear_generated_files(output_dir: Path) -> int:
    removed = 0
    if output_dir.exists():
        for pattern in ("*.csv", "manifest.json"):
            for path in output_dir.glob(pattern):
                path.unlink()
                removed += 1

    report_path = REPO_ROOT / "runtime" / "seed_load_report.json"
    if report_path.exists():
        report_path.unlink()
        removed += 1

    return removed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reset generated telco seed artifacts and the Snowflake landing objects they populate."
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent / "output"),
        help="Directory that contains generated CSV files and manifest.json.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Required to confirm the destructive DROP DATABASE against the configured Snowflake target.",
    )
    args = parser.parse_args()

    database = get_env("SNOWFLAKE_DATABASE", required=True)
    account = get_env("SNOWFLAKE_ACCOUNT", required=True)
    role = get_env("SNOWFLAKE_ROLE", required=True)

    if not args.yes:
        print(
            f"Refusing to drop database {fq_name(database)} on account {account} as role {role}.\n"
            "Re-run with --yes to confirm.",
            file=sys.stderr,
        )
        sys.exit(1)

    output_dir = Path(args.output_dir).resolve()
    removed_files = clear_generated_files(output_dir)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            execute_many(cursor, build_reset_statements())

    print(f"Reset Snowflake seed state and removed {removed_files} generated local seed artifact(s).")


if __name__ == "__main__":
    main()
