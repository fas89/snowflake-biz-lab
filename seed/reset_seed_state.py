from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config.snowflake_utils import execute_many, fq_name, get_connection, get_env  # noqa: E402


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
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    removed_files = clear_generated_files(output_dir)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            execute_many(cursor, build_reset_statements())

    print(f"Reset Snowflake seed state and removed {removed_files} generated local seed artifact(s).")


if __name__ == "__main__":
    main()
