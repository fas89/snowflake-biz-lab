from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from config.snowflake_utils import fq_name, get_env, quote_ident, sql_string
from seed.telco_seed_data import TABLE_SPECS

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = REPO_ROOT / "governance" / "metadata.yml"
DEFAULT_SQL_PATH = REPO_ROOT / "governance" / "sql" / "rendered_metadata.sql"


def load_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> dict[str, Any]:
    manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise RuntimeError("Governance manifest must be a YAML mapping.")
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest: dict[str, Any]) -> None:
    for key in ("tag_definitions", "contacts", "dataset", "table_defaults", "tables"):
        if key not in manifest:
            raise RuntimeError(f"Governance manifest is missing required top-level key: {key}")

    manifest_tables = manifest["tables"]
    expected_tables = set(TABLE_SPECS)
    actual_tables = set(manifest_tables)
    if expected_tables != actual_tables:
        missing = sorted(expected_tables - actual_tables)
        extra = sorted(actual_tables - expected_tables)
        raise RuntimeError(f"Governance manifest table mismatch. Missing={missing}, extra={extra}")

    tag_definitions = manifest["tag_definitions"]
    dataset_tags = manifest["dataset"].get("tags", {})
    for tag_name in dataset_tags:
        if tag_name not in tag_definitions:
            raise RuntimeError(f"Dataset tag '{tag_name}' is not defined in tag_definitions.")

    for table_name, spec in TABLE_SPECS.items():
        table_cfg = manifest_tables[table_name]
        if "comment" not in table_cfg:
            raise RuntimeError(f"Table '{table_name}' is missing a comment.")

        for tag_name in table_cfg.get("tags", {}):
            if tag_name not in tag_definitions:
                raise RuntimeError(f"Table '{table_name}' references undefined tag '{tag_name}'.")

        columns_cfg = table_cfg.get("columns", {})
        expected_columns = [column.name for column in spec.columns]
        if set(columns_cfg) != set(expected_columns):
            missing = [name for name in expected_columns if name not in columns_cfg]
            extra = sorted(set(columns_cfg) - set(expected_columns))
            raise RuntimeError(
                f"Column metadata mismatch for '{table_name}'. Missing={missing}, extra={extra}"
            )

        for column_name, column_cfg in columns_cfg.items():
            if "comment" not in column_cfg:
                raise RuntimeError(f"Column '{table_name}.{column_name}' is missing a comment.")
            tags = column_cfg.get("tags", {})
            for required_tag in ("semantic_type", "sensitivity", "identifier_role"):
                if required_tag not in tags:
                    raise RuntimeError(
                        f"Column '{table_name}.{column_name}' is missing required tag '{required_tag}'."
                    )
            for tag_name in tags:
                if tag_name not in tag_definitions:
                    raise RuntimeError(
                        f"Column '{table_name}.{column_name}' references undefined tag '{tag_name}'."
                    )


def database_name() -> str:
    return get_env("SNOWFLAKE_DATABASE", "TELCO_LAB")


def stage_schema_name() -> str:
    return get_env("SNOWFLAKE_STAGE_SCHEMA", "TELCO_STAGE_LOAD")


def governance_schema_name() -> str:
    return get_env("SNOWFLAKE_GOVERNANCE_SCHEMA", "TELCO_GOVERNANCE")


def stage_schema_fqn() -> str:
    return fq_name(database_name(), stage_schema_name())


def governance_schema_fqn() -> str:
    return fq_name(database_name(), governance_schema_name())


def stage_table_fqn(table_name: str) -> str:
    return fq_name(database_name(), stage_schema_name(), table_name)


def governance_tag_fqn(tag_name: str) -> str:
    return fq_name(database_name(), governance_schema_name(), tag_name)


def governance_contact_fqn(contact_name: str) -> str:
    return fq_name(database_name(), governance_schema_name(), contact_name)


def stage_schema_string() -> str:
    return sql_string(fq_name(database_name(), stage_schema_name()))


def stage_table_string(table_name: str) -> str:
    return sql_string(fq_name(database_name(), stage_schema_name(), table_name))


def information_schema_fqn() -> str:
    return fq_name(database_name(), "INFORMATION_SCHEMA")


def merge_table_tags(manifest: dict[str, Any], table_cfg: dict[str, Any]) -> dict[str, str]:
    tags = dict(manifest["dataset"].get("tags", {}))
    tags.update(table_cfg.get("tags", {}))
    return tags


def merge_table_contacts(manifest: dict[str, Any], table_cfg: dict[str, Any]) -> dict[str, str]:
    contacts = dict(manifest["table_defaults"].get("contacts", {}))
    contacts.update(table_cfg.get("contacts", {}))
    return contacts


def merge_table_classification(manifest: dict[str, Any], table_cfg: dict[str, Any]) -> dict[str, Any]:
    config = dict(manifest["table_defaults"].get("classification", {}))
    config.update(table_cfg.get("classification", {}))
    return config


def merge_table_dmf(manifest: dict[str, Any], table_cfg: dict[str, Any]) -> dict[str, Any]:
    config = dict(manifest["table_defaults"].get("dmf", {}))
    config.update(table_cfg.get("dmf", {}))
    return config


def _render_tag_create_statement(tag_name: str, tag_cfg: dict[str, Any]) -> str:
    parts = [f"CREATE TAG IF NOT EXISTS {governance_tag_fqn(tag_name)}"]
    allowed_values = tag_cfg.get("allowed_values", [])
    if allowed_values:
        parts.append(
            "ALLOWED_VALUES " + ", ".join(sql_string(str(value)) for value in allowed_values)
        )
    if tag_cfg.get("comment"):
        parts.append(f"COMMENT = {sql_string(tag_cfg['comment'])}")
    return " ".join(parts)


def _render_contact_create_statement(contact_name: str, contact_cfg: dict[str, Any]) -> str:
    method = contact_cfg["method"].upper()
    value = contact_cfg["value"]
    if method not in {"EMAIL_DISTRIBUTION_LIST", "URL"}:
        raise RuntimeError(f"Unsupported contact method '{method}' for '{contact_name}'.")
    comment_clause = ""
    if contact_cfg.get("comment"):
        comment_clause = f" COMMENT = {sql_string(contact_cfg['comment'])}"
    return (
        f"CREATE CONTACT IF NOT EXISTS {governance_contact_fqn(contact_name)} "
        f"{method} = {sql_string(value)}{comment_clause}"
    )


def _render_set_tags_statement(object_type: str, object_fqn: str, tags: dict[str, str]) -> str | None:
    if not tags:
        return None
    assignments = ", ".join(
        f"{governance_tag_fqn(tag_name)} = {sql_string(str(tag_value))}"
        for tag_name, tag_value in tags.items()
    )
    return f"ALTER {object_type} {object_fqn} SET TAG {assignments}"


def _render_set_contacts_statement(
    object_type: str,
    object_fqn: str,
    contacts: dict[str, str],
) -> str | None:
    if not contacts:
        return None
    assignments = ", ".join(
        f"{purpose} = {governance_contact_fqn(contact_name)}"
        for purpose, contact_name in contacts.items()
    )
    return f"ALTER {object_type} {object_fqn} SET CONTACT {assignments}"


def _render_classification_statement(table_name: str, classification_cfg: dict[str, Any]) -> str | None:
    if not classification_cfg.get("enabled", False):
        return None

    if classification_cfg.get("profile"):
        options = sql_string(str(classification_cfg["profile"]))
    else:
        options_parts: list[str] = []
        sample_count = classification_cfg.get("sample_count")
        if sample_count is not None:
            options_parts.append(f"'sample_count': {int(sample_count)}")
        if "auto_tag" in classification_cfg:
            options_parts.append(
                f"'auto_tag': {'true' if bool(classification_cfg['auto_tag']) else 'false'}"
            )
        if classification_cfg.get("use_all_custom_classifiers"):
            options_parts.append("'use_all_custom_classifiers': true")
        options = "{" + ", ".join(options_parts) + "}" if options_parts else "null"

    return f"CALL SYSTEM$CLASSIFY({stage_table_string(table_name)}, {options})"


def _render_expectations(expectations: list[dict[str, str]]) -> str:
    return ", ".join(
        f"{expectation['name']} ({expectation['expression']})" for expectation in expectations
    )


def _render_dmf_metric_statement(table_name: str, metric_cfg: dict[str, Any]) -> str:
    metric_name = metric_cfg["name"]
    arguments = [quote_ident(argument) for argument in metric_cfg.get("arguments", [])]
    if metric_cfg.get("lambda_expression"):
        arguments.append(str(metric_cfg["lambda_expression"]))
    arguments_sql = ", ".join(arguments)
    statement = (
        f"ALTER TABLE {stage_table_fqn(table_name)} "
        f"ADD DATA METRIC FUNCTION {metric_name} ON ({arguments_sql})"
    )
    expectations = metric_cfg.get("expectations", [])
    if expectations:
        statement += f" EXPECTATION {_render_expectations(expectations)}"
    return statement


def render_sql_sections(manifest: dict[str, Any]) -> dict[str, list[str]]:
    core_statements = [
        f"CREATE DATABASE IF NOT EXISTS {fq_name(database_name())}",
        f"CREATE SCHEMA IF NOT EXISTS {stage_schema_fqn()}",
        f"CREATE SCHEMA IF NOT EXISTS {governance_schema_fqn()}",
    ]

    for tag_name, tag_cfg in manifest["tag_definitions"].items():
        core_statements.append(_render_tag_create_statement(tag_name, tag_cfg))
    for contact_name, contact_cfg in manifest["contacts"].items():
        core_statements.append(_render_contact_create_statement(contact_name, contact_cfg))

    dataset = manifest["dataset"]
    schema_statements = [
        f"COMMENT ON SCHEMA {stage_schema_fqn()} IS {sql_string(dataset['schema_comment'])}",
    ]
    schema_tag_statement = _render_set_tags_statement("SCHEMA", stage_schema_fqn(), dataset.get("tags", {}))
    if schema_tag_statement:
        schema_statements.append(schema_tag_statement)
    schema_contact_statement = _render_set_contacts_statement(
        "SCHEMA",
        stage_schema_fqn(),
        dataset.get("contacts", {}),
    )
    if schema_contact_statement:
        schema_statements.append(schema_contact_statement)

    table_statements: list[str] = []
    classification_statements: list[str] = []
    dmf_statements: list[str] = []

    for table_name, table_cfg in manifest["tables"].items():
        table_fqn = stage_table_fqn(table_name)
        table_statements.append(
            f"COMMENT ON TABLE {table_fqn} IS {sql_string(table_cfg['comment'])}"
        )
        table_tags = merge_table_tags(manifest, table_cfg)
        table_tag_statement = _render_set_tags_statement("TABLE", table_fqn, table_tags)
        if table_tag_statement:
            table_statements.append(table_tag_statement)

        table_contacts = merge_table_contacts(manifest, table_cfg)
        table_contact_statement = _render_set_contacts_statement("TABLE", table_fqn, table_contacts)
        if table_contact_statement:
            table_statements.append(table_contact_statement)

        for column_name, column_cfg in table_cfg.get("columns", {}).items():
            table_statements.append(
                f"COMMENT ON COLUMN {table_fqn}.{quote_ident(column_name)} "
                f"IS {sql_string(column_cfg['comment'])}"
            )
            column_tags = column_cfg.get("tags", {})
            if column_tags:
                assignments = ", ".join(
                    f"{governance_tag_fqn(tag_name)} = {sql_string(str(tag_value))}"
                    for tag_name, tag_value in column_tags.items()
                )
                table_statements.append(
                    f"ALTER TABLE {table_fqn} MODIFY COLUMN {quote_ident(column_name)} "
                    f"SET TAG {assignments}"
                )

        classification_cfg = merge_table_classification(manifest, table_cfg)
        classification_statement = _render_classification_statement(table_name, classification_cfg)
        if classification_statement:
            classification_statements.append(classification_statement)

        dmf_cfg = merge_table_dmf(manifest, table_cfg)
        schedule = dmf_cfg.get("schedule")
        metrics = dmf_cfg.get("metrics", [])
        if schedule and metrics:
            dmf_statements.append(
                f"ALTER TABLE {table_fqn} SET DATA_METRIC_SCHEDULE = {sql_string(str(schedule))}"
            )
        for metric_cfg in metrics:
            dmf_statements.append(_render_dmf_metric_statement(table_name, metric_cfg))

    return {
        "core": core_statements,
        "schema": schema_statements,
        "tables": table_statements,
        "classification": classification_statements,
        "dmf": dmf_statements,
    }


def write_sql_bundle(path: Path, sections: dict[str, list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    chunks: list[str] = []
    for section_name, statements in sections.items():
        chunks.append(f"-- {section_name}")
        for statement in statements:
            chunks.append(statement.rstrip(";") + ";")
        chunks.append("")
    path.write_text("\n".join(chunks).rstrip() + "\n", encoding="utf-8")
