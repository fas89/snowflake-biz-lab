from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config.snowflake_utils import env_bool, fetch_all_dicts, get_connection, sql_string  # noqa: E402
from governance.metadata_utils import (  # noqa: E402
    DEFAULT_MANIFEST_PATH,
    information_schema_fqn,
    load_manifest,
    merge_table_classification,
    merge_table_contacts,
    merge_table_dmf,
    merge_table_tags,
    stage_schema_fqn,
    stage_schema_name,
    stage_schema_string,
    stage_table_fqn,
    stage_table_string,
)


def _normalize_tag_rows(rows: list[dict[str, Any]]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for row in rows:
        normalized[str(row["tag_name"]).lower()] = str(row["tag_value"])
    return normalized


def _normalize_contact_rows(rows: list[dict[str, Any]]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for row in rows:
        normalized[str(row["purpose"]).upper()] = (
            str(row.get("email_distribution_list") or row.get("url") or row.get("user") or "")
        )
    return normalized


def _fetch_table_tags(cursor: Any, table_name: str) -> dict[str, str]:
    rows = fetch_all_dicts(
        cursor,
        f"SELECT tag_name, tag_value FROM TABLE({information_schema_fqn()}.TAG_REFERENCES("
        f"{stage_table_string(table_name)}, 'TABLE'))",
    )
    return _normalize_tag_rows(rows)


def _fetch_column_tags(cursor: Any, table_name: str) -> dict[str, dict[str, str]]:
    rows = fetch_all_dicts(
        cursor,
        f"SELECT column_name, tag_name, tag_value FROM TABLE({information_schema_fqn()}.TAG_REFERENCES_ALL_COLUMNS("
        f"{stage_table_string(table_name)}, 'TABLE'))",
    )
    normalized: dict[str, dict[str, str]] = {}
    for row in rows:
        column_name = str(row["column_name"]).lower()
        normalized.setdefault(column_name, {})[str(row["tag_name"]).lower()] = str(row["tag_value"])
    return normalized


def _fetch_contacts(cursor: Any, object_name: str, object_type: str) -> dict[str, str]:
    rows = fetch_all_dicts(
        cursor,
        "SELECT purpose, email_distribution_list, url, user "
        f"FROM TABLE(SNOWFLAKE.CORE.GET_CONTACTS({sql_string(object_name)}, {sql_string(object_type)}))",
    )
    return _normalize_contact_rows(rows)


def _fetch_table_comment(cursor: Any, table_name: str) -> str:
    rows = fetch_all_dicts(
        cursor,
        "SELECT comment FROM "
        f"{information_schema_fqn()}.TABLES "
        f"WHERE table_schema = UPPER({sql_string(stage_schema_name())}) "
        f"AND table_name = UPPER({sql_string(table_name)})",
    )
    return str(rows[0]["comment"] or "")


def _fetch_column_comments(cursor: Any, table_name: str) -> dict[str, str]:
    rows = fetch_all_dicts(
        cursor,
        "SELECT column_name, comment FROM "
        f"{information_schema_fqn()}.COLUMNS "
        f"WHERE table_schema = UPPER({sql_string(stage_schema_name())}) "
        f"AND table_name = UPPER({sql_string(table_name)})",
    )
    return {str(row["column_name"]).lower(): str(row["comment"] or "") for row in rows}


def _fetch_schema_comment(cursor: Any) -> str:
    rows = fetch_all_dicts(
        cursor,
        "SELECT comment FROM "
        f"{information_schema_fqn()}.SCHEMATA "
        f"WHERE schema_name = UPPER({sql_string(stage_schema_name())})",
    )
    return str(rows[0]["comment"] or "")


def _fetch_schema_tags(cursor: Any) -> dict[str, str]:
    rows = fetch_all_dicts(
        cursor,
        f"SELECT tag_name, tag_value FROM TABLE({information_schema_fqn()}.TAG_REFERENCES("
        f"{stage_schema_string()}, 'SCHEMA'))",
    )
    return _normalize_tag_rows(rows)


def _fetch_table_dmf_names(cursor: Any, table_name: str) -> set[str]:
    rows = fetch_all_dicts(
        cursor,
        "SELECT metric_name FROM TABLE("
        f"{information_schema_fqn()}.DATA_METRIC_FUNCTION_REFERENCES("
        f"REF_ENTITY_NAME => {stage_table_string(table_name)}, REF_ENTITY_DOMAIN => 'TABLE'))",
    )
    return {str(row["metric_name"]).upper() for row in rows}


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

            schema_tags = _fetch_schema_tags(cursor)
            for tag_name, expected_value in schema_cfg.get("tags", {}).items():
                if schema_tags.get(tag_name.lower()) != str(expected_value):
                    failures.append(f"Schema tag '{tag_name}' is missing or has the wrong value.")

            schema_contacts = _fetch_contacts(cursor, stage_schema_fqn(), "SCHEMA")
            for purpose, contact_name in schema_cfg.get("contacts", {}).items():
                contact_cfg = manifest["contacts"][contact_name]
                expected_value = str(contact_cfg["value"])
                if schema_contacts.get(purpose.upper()) != expected_value:
                    failures.append(f"Schema contact '{purpose}' is missing or has the wrong value.")

            for table_name, table_cfg in manifest["tables"].items():
                table_comment = _fetch_table_comment(cursor, table_name)
                if table_comment != table_cfg["comment"]:
                    failures.append(f"Table comment mismatch for '{table_name}'.")

                table_tags = _fetch_table_tags(cursor, table_name)
                for tag_name, expected_value in merge_table_tags(manifest, table_cfg).items():
                    if table_tags.get(tag_name.lower()) != str(expected_value):
                        failures.append(
                            f"Table tag '{tag_name}' mismatch for '{table_name}'."
                        )

                table_contacts = _fetch_contacts(cursor, stage_table_fqn(table_name), "TABLE")
                for purpose, contact_name in merge_table_contacts(manifest, table_cfg).items():
                    contact_cfg = manifest["contacts"][contact_name]
                    expected_value = str(contact_cfg["value"])
                    if table_contacts.get(purpose.upper()) != expected_value:
                        failures.append(
                            f"Table contact '{purpose}' mismatch for '{table_name}'."
                        )

                column_comments = _fetch_column_comments(cursor, table_name)
                column_tags = _fetch_column_tags(cursor, table_name)
                for column_name, column_cfg in table_cfg["columns"].items():
                    if column_comments.get(column_name.lower()) != column_cfg["comment"]:
                        failures.append(
                            f"Column comment mismatch for '{table_name}.{column_name}'."
                        )
                    expected_tags = column_cfg.get("tags", {})
                    actual_tags = column_tags.get(column_name.lower(), {})
                    for tag_name, expected_value in expected_tags.items():
                        if actual_tags.get(tag_name.lower()) != str(expected_value):
                            failures.append(
                                f"Column tag '{tag_name}' mismatch for '{table_name}.{column_name}'."
                            )

                if env_bool("SNOWFLAKE_ENABLE_DMF", False):
                    actual_metric_names = _fetch_table_dmf_names(cursor, table_name)
                    expected_metric_names = {
                        metric["name"].split(".")[-1].upper()
                        for metric in merge_table_dmf(manifest, table_cfg).get("metrics", [])
                    }
                    if not expected_metric_names.issubset(actual_metric_names):
                        failures.append(f"DMF associations are incomplete for '{table_name}'.")

                if env_bool("SNOWFLAKE_ENABLE_CLASSIFICATION", False):
                    classification_cfg = merge_table_classification(manifest, table_cfg)
                    if classification_cfg.get("enabled") and classification_cfg.get("auto_tag", False):
                        actual_tags = column_tags
                        classified = any(
                            "semantic_category" in tags or "privacy_category" in tags
                            for tags in actual_tags.values()
                        )
                        if not classified:
                            print(
                                f"Warning: no classification system tags found on '{table_name}'. "
                                "This can happen when classification is disabled by edition or privilege."
                            )

    if failures:
        raise RuntimeError("Metadata verification failed:\n- " + "\n- ".join(failures))

    print("Verified schema, table, column, contact, and tag metadata in Snowflake.")
    if env_bool("SNOWFLAKE_ENABLE_DMF", False):
        print("Verified DMF associations in Snowflake.")


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
