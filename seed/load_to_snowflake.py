from __future__ import annotations

import argparse
import json
from pathlib import Path

from config.snowflake_utils import execute_many, fq_name, get_connection, get_env, quote_ident
from seed.telco_seed_data import TABLE_SPECS


def build_ddl_statements() -> list[str]:
    database = get_env("SNOWFLAKE_DATABASE", required=True)
    stage_schema = get_env("SNOWFLAKE_STAGE_SCHEMA", required=True)
    internal_stage = get_env("SNOWFLAKE_INTERNAL_STAGE", "TELCO_SEED_STAGE")
    file_format = get_env("SNOWFLAKE_FILE_FORMAT", "TELCO_SEED_CSV")

    statements = [
        f"CREATE DATABASE IF NOT EXISTS {fq_name(database)}",
        f"CREATE SCHEMA IF NOT EXISTS {fq_name(database, stage_schema)}",
        (
            f"CREATE OR REPLACE FILE FORMAT {fq_name(database, stage_schema, file_format)} "
            "TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '\"' SKIP_HEADER = 1 "
            "NULL_IF = ('\\\\N') EMPTY_FIELD_AS_NULL = TRUE"
        ),
        (
            f"CREATE STAGE IF NOT EXISTS {fq_name(database, stage_schema, internal_stage)} "
            f"FILE_FORMAT = {fq_name(database, stage_schema, file_format)}"
        ),
    ]
    for spec in TABLE_SPECS.values():
        column_sql = ", ".join(
            f"{quote_ident(column.name)} {column.snowflake_type}" for column in spec.columns
        )
        statements.append(
            f"CREATE TABLE IF NOT EXISTS {fq_name(database, stage_schema, spec.name)} ({column_sql})"
        )
    return statements


def load_files(output_dir: Path) -> None:
    database = get_env("SNOWFLAKE_DATABASE", required=True)
    stage_schema = get_env("SNOWFLAKE_STAGE_SCHEMA", required=True)
    internal_stage = get_env("SNOWFLAKE_INTERNAL_STAGE", "TELCO_SEED_STAGE")
    file_format = get_env("SNOWFLAKE_FILE_FORMAT", "TELCO_SEED_CSV")
    report: dict[str, dict[str, object]] = {}

    with get_connection() as conn:
        with conn.cursor() as cursor:
            execute_many(cursor, build_ddl_statements())
            for table_name in TABLE_SPECS:
                csv_path = output_dir / f"{table_name}.csv"
                if not csv_path.exists():
                    raise FileNotFoundError(f"Missing seed file: {csv_path}")

                stage_name = fq_name(database, stage_schema, internal_stage)
                table_name_fq = fq_name(database, stage_schema, table_name)

                cursor.execute(f"TRUNCATE TABLE {table_name_fq}")
                cursor.execute(
                    f"PUT file://{csv_path.as_posix()} @{stage_name} AUTO_COMPRESS=TRUE OVERWRITE=TRUE"
                )
                put_result = cursor.fetchall()

                copy_sql = (
                    f"COPY INTO {table_name_fq} FROM @{stage_name}/{csv_path.name}.gz "
                    f"FILE_FORMAT = (FORMAT_NAME = {fq_name(database, stage_schema, file_format)}) "
                    "ON_ERROR = 'ABORT_STATEMENT'"
                )
                cursor.execute(copy_sql)
                copy_result = cursor.fetchall()

                report[table_name] = {
                    "put_result": put_result,
                    "copy_result": copy_result,
                }

    report_path = REPO_ROOT / "runtime" / "seed_load_report.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"Wrote Snowflake load report to {report_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Load generated telco CSV seeds into Snowflake.")
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent / "output"),
        help="Directory that contains generated CSV files.",
    )
    args = parser.parse_args()
    load_files(Path(args.output_dir).resolve())


if __name__ == "__main__":
    main()
