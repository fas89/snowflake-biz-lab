from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from config.snowflake_utils import fetch_all_dicts, get_connection, sql_string
from governance.metadata_utils import (
    DEFAULT_MANIFEST_PATH,
    information_schema_fqn,
    load_manifest,
    stage_schema_name,
)


def _fetch_table_comment(cursor: Any, table_name: str) -> str:
    rows = fetch_all_dicts(
        cursor,
        "SELECT comment FROM "
        f"{information_schema_fqn()}.TABLES "
        f"WHERE table_schema = {sql_string(stage_schema_name())} "
        f"AND table_name = {sql_string(table_name)}",
    )
    return str(rows[0]["comment"] or "")


def _fetch_column_comments(cursor: Any, table_name: str) -> dict[str, str]:
    rows = fetch_all_dicts(
        cursor,
        "SELECT column_name, comment FROM "
        f"{information_schema_fqn()}.COLUMNS "
        f"WHERE table_schema = {sql_string(stage_schema_name())} "
        f"AND table_name = {sql_string(table_name)}",
    )
    return {str(row["column_name"]).lower(): str(row["comment"] or "") for row in rows}


def _fetch_schema_comment(cursor: Any) -> str:
    rows = fetch_all_dicts(
        cursor,
        "SELECT comment FROM "
        f"{information_schema_fqn()}.SCHEMATA "
        f"WHERE schema_name = {sql_string(stage_schema_name())}",
    )
    return str(rows[0]["comment"] or "")


def verify_manifest(manifest: dict[str, Any]) -> None:
    print(f"Validated governance manifest for {len(manifest['tables'])} tables.")


def verify_snowflake(manifest: dict[str, Any]) -> None:
    schema_cfg = manifest["dataset"]
    failures: list[str] = []

    with get_connection() as conn:
        with conn.cursor() as cursor:
            schema_comment = _fetch_schema_comment(cursor)
            if schema_comment != schema_cfg["schema_comment"]:
                failures.append("Schema comment does not match manifest.")

            for table_name, table_cfg in manifest["tables"].items():
                table_comment = _fetch_table_comment(cursor, table_name)
                if table_comment != table_cfg["comment"]:
                    failures.append(f"Table comment mismatch for '{table_name}'.")

                column_comments = _fetch_column_comments(cursor, table_name)
                for column_name, column_cfg in table_cfg["columns"].items():
                    if column_comments.get(column_name.lower()) != column_cfg["comment"]:
                        failures.append(
                            f"Column comment mismatch for '{table_name}.{column_name}'."
                        )

    if failures:
        raise RuntimeError("Metadata verification failed:\n- " + "\n- ".join(failures))

    print("Verified schema, table, and column comments in Snowflake.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Snowflake Horizon metadata for the telco landing schema.")
    parser.add_argument(
        "--manifest-path",
        default=str(DEFAULT_MANIFEST_PATH),
        help="Path to the governance metadata manifest.",
    )
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help="Validate the metadata manifest structure without querying Snowflake.",
    )
    args = parser.parse_args()

    manifest = load_manifest(Path(args.manifest_path).resolve())
    verify_manifest(manifest)

    if not args.manifest_only:
        verify_snowflake(manifest)


if __name__ == "__main__":
    main()
