from __future__ import annotations

import argparse
import json
from pathlib import Path

from config.snowflake_utils import fetch_all_dicts, fq_name, get_connection, get_env
from seed.telco_seed_data import TABLE_SPECS


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def verify_local_artifacts(output_dir: Path) -> dict[str, int]:
    manifest_path = output_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_counts: dict[str, int] = {}

    for table_name, table_meta in manifest["tables"].items():
        csv_path = output_dir / table_meta["file"]
        actual_count = count_csv_rows(csv_path)
        expected_count = table_meta["row_count"]
        if actual_count != expected_count:
            raise RuntimeError(
                f"Row-count mismatch for {table_name}: expected {expected_count}, found {actual_count}"
            )
        expected_counts[table_name] = expected_count
    return expected_counts


def verify_snowflake(expected_counts: dict[str, int]) -> None:
    database = get_env("SNOWFLAKE_DATABASE", required=True)
    stage_schema = get_env("SNOWFLAKE_STAGE_SCHEMA", required=True)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            for table_name, expected_count in expected_counts.items():
                table_name_fq = fq_name(database, stage_schema, table_name)
                rows = fetch_all_dicts(cursor, f"SELECT COUNT(*) AS row_count FROM {table_name_fq}")
                actual_count = int(rows[0]["row_count"])
                if actual_count != expected_count:
                    raise RuntimeError(
                        f"Snowflake row-count mismatch for {table_name}: expected {expected_count}, found {actual_count}"
                    )
                print(f"  {table_name}: {actual_count} rows")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify generated telco seed files and Snowflake loads.")
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent / "output"),
        help="Directory that contains generated CSV files.",
    )
    parser.add_argument(
        "--skip-snowflake",
        action="store_true",
        help="Only verify the local CSV artifacts and manifest.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    expected_counts = verify_local_artifacts(output_dir)
    print(f"Verified {len(expected_counts)} local seed files.")

    if not args.skip_snowflake:
        verify_snowflake(expected_counts)


if __name__ == "__main__":
    main()
