from __future__ import annotations

import argparse
import json
from pathlib import Path

from seed.postgres_utils import (
    fq_name,
    get_connection,
    quote_ident,
    snowflake_type_to_postgres,
    source_schema,
)
from seed.telco_seed_data import TABLE_SPECS

REPO_ROOT = Path(__file__).resolve().parents[1]


def build_ddl_statements() -> list[str]:
    schema = source_schema()
    statements = [f"CREATE SCHEMA IF NOT EXISTS {quote_ident(schema)}"]
    for spec in TABLE_SPECS.values():
        column_sql = ", ".join(
            f"{quote_ident(column.name)} {snowflake_type_to_postgres(column.snowflake_type)}"
            for column in spec.columns
        )
        statements.append(
            f"CREATE TABLE IF NOT EXISTS {fq_name(schema, spec.name)} ({column_sql})"
        )
    return statements


def load_files(output_dir: Path) -> dict[str, dict[str, object]]:
    schema = source_schema()
    report: dict[str, dict[str, object]] = {}

    with get_connection() as conn:
        with conn.cursor() as cursor:
            for statement in build_ddl_statements():
                cursor.execute(statement)
            conn.commit()

            for table_name in TABLE_SPECS:
                csv_path = output_dir / f"{table_name}.csv"
                if not csv_path.exists():
                    raise FileNotFoundError(f"Missing seed file: {csv_path}")

                qualified = fq_name(schema, table_name)
                cursor.execute(f"TRUNCATE TABLE {qualified}")
                with csv_path.open("r", encoding="utf-8") as handle:
                    cursor.copy_expert(
                        f"COPY {qualified} FROM STDIN WITH (FORMAT csv, HEADER true, NULL '\\N')",
                        handle,
                    )
                cursor.execute(f"SELECT count(*) FROM {qualified}")
                count = cursor.fetchone()[0]
                report[table_name] = {"row_count": count, "source_file": csv_path.name}
            conn.commit()

    report_path = REPO_ROOT / "runtime" / "seed_load_postgres_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"Wrote Postgres load report to {report_path}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load generated telco CSV seeds into the Postgres source database."
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent / "output"),
        help="Directory that contains generated CSV files.",
    )
    args = parser.parse_args()
    load_files(Path(args.output_dir).resolve())


if __name__ == "__main__":
    main()
