from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from config.snowflake_utils import fq_name, get_env, quote_ident, sql_string
from seed.telco_seed_data import TABLE_SPECS, TableSpec

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = REPO_ROOT / "governance" / "metadata.yml"
DEFAULT_SQL_PATH = REPO_ROOT / "governance" / "sql" / "rendered_metadata.sql"


def load_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> dict[str, Any]:
    manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise RuntimeError("Governance manifest must be a YAML mapping.")
    manifest = complete_manifest(manifest)
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


def infer_record_grain(table_name: str) -> str:
    if table_name in {"usage_event", "app_event", "customer_interaction", "service_lifecycle_event"}:
        return "event_level"
    if table_name in {"invoice", "invoice_charge", "payment", "agreement", "service_order", "trouble_ticket"}:
        return "document_level"
    if table_name in {"contact_medium", "party_role", "subscription", "product_inventory", "resource", "sim_card"}:
        return "assignment_level"
    return "entity_level"


def infer_primary_key_column(table_name: str, spec: TableSpec) -> str:
    for column in spec.columns:
        if column.name == f"{table_name}_id":
            return column.name
    for column in spec.columns:
        if column.name.endswith("_id"):
            return column.name
    return spec.columns[0].name


def infer_semantic_type(column_name: str) -> str:
    if column_name == "address_id":
        return "address_identifier"
    if column_name in {"street_name", "city", "region_code", "postal_code", "country_code"}:
        return "address_attribute"
    if column_name == "contact_medium_id":
        return "contact_identifier"
    if column_name == "medium_value":
        return "contact_value"
    if column_name == "party_role_id":
        return "role_identifier"
    if column_name == "role_type":
        return "role_type"
    if column_name in {"product_offering_id", "product_id"}:
        return "product_identifier"
    if column_name == "resource_id":
        return "resource_identifier"
    if column_name in {"resource_type", "resource_name"}:
        return "resource_attribute"
    if column_name == "ticket_id":
        return "ticket_identifier"
    if column_name == "charge_id":
        return "charge_identifier"
    if column_name in {"charge_description"}:
        return "narrative_text"
    if column_name in {"severity"}:
        return "priority_code"
    if column_name in {"party_id", "individual_id"}:
        return "party_identifier"
    if column_name == "account_id":
        return "account_identifier"
    if column_name == "account_number":
        return "account_number"
    if column_name == "date_of_birth":
        return "birth_date"
    if column_name == "agreement_id":
        return "contract_identifier"
    if column_name in {"created_at", "assigned_at", "activated_at", "registered_at"}:
        return "created_timestamp"
    if column_name in {
        "invoice_date",
        "due_date",
        "payment_date",
        "signed_date",
        "effective_date",
        "termination_date",
        "start_date",
        "end_date",
        "renewal_date",
        "valid_from",
        "valid_to",
        "charge_date",
    }:
        return "date_value"
    if column_name in {"price_chf", "total_amount_chf", "amount_chf"}:
        return "currency_amount"
    if column_name == "device_id":
        return "device_identifier"
    if column_name == "email":
        return "email_handle"
    if column_name in {"usage_id", "app_event_id", "interaction_id", "lifecycle_event_id"}:
        return "event_identifier"
    if column_name in {
        "updated_at",
        "terminated_at",
        "event_timestamp",
        "interaction_timestamp",
        "opened_at",
        "resolved_at",
        "order_date",
        "fulfillment_date",
    }:
        return "event_timestamp"
    if column_name == "invoice_id":
        return "invoice_identifier"
    if column_name == "order_id":
        return "order_identifier"
    if column_name == "payment_id":
        return "payment_identifier"
    if column_name in {"first_name", "last_name"}:
        return "person_name"
    if column_name == "msisdn":
        return "phone_number"
    if column_name in {"name", "model", "manufacturer", "event_reason"}:
        return "product_attribute"
    if column_name == "service_id":
        return "service_identifier"
    if column_name == "sim_id":
        return "sim_identifier"
    if column_name in {
        "status",
        "rating_status",
        "resource_status",
    }:
        return "status_code"
    if column_name in {"quantity", "session_minutes", "data_limit_gb", "voice_limit_min", "preference_rank"}:
        return "usage_measure"
    return "category_code"


def infer_sensitivity(column_name: str) -> str:
    if column_name in {
        "first_name",
        "last_name",
        "email",
        "date_of_birth",
        "medium_value",
        "street_name",
        "city",
        "region_code",
        "postal_code",
        "country_code",
        "msisdn",
    }:
        return "restricted_contact"
    if column_name.endswith("_id") or column_name in {
        "account_number",
        "imei",
        "iccid",
        "invoice_number",
    }:
        return "restricted_identifier"
    if column_name in {"name", "category", "data_limit_gb", "voice_limit_min", "price_chf"}:
        return "public_synthetic"
    return "internal_operational"


def infer_identifier_role(column_name: str, primary_key: str) -> str:
    if column_name == primary_key:
        return "primary_key"
    if column_name in {"account_number", "email", "msisdn", "iccid", "imei", "invoice_number"}:
        return "natural_key"
    if column_name.endswith("_id"):
        return "foreign_key"
    return "descriptive"


def humanize_identifier(value: str) -> str:
    return value.replace("_", " ")


def default_column_comment(table_name: str, column_name: str, primary_key: str) -> str:
    if column_name == primary_key:
        return f"Stable synthetic identifier for the {humanize_identifier(table_name)} record."
    if column_name.endswith("_id"):
        return f"Reference to the related {humanize_identifier(column_name[:-3])} record."
    if column_name in {"status", "rating_status", "resource_status"}:
        return f"Lifecycle or operational status for the {humanize_identifier(table_name)} record."
    if column_name in {"created_at", "assigned_at", "activated_at", "registered_at"}:
        return f"Timestamp when the {humanize_identifier(table_name)} record was created or assigned."
    if column_name in {"updated_at", "terminated_at", "event_timestamp", "interaction_timestamp", "opened_at", "resolved_at"}:
        return f"Timestamp describing when the {humanize_identifier(column_name)} occurred."
    if column_name.endswith("_date") or column_name in {"valid_from", "valid_to"}:
        return f"Date value for {humanize_identifier(column_name)} on the {humanize_identifier(table_name)} record."
    if column_name in {"first_name", "last_name"}:
        return f"Synthetic {humanize_identifier(column_name)} for the customer contact."
    if column_name == "email":
        return "Synthetic email address used for contact and governance demonstrations."
    if column_name == "medium_value":
        return "Synthetic contact detail captured for the selected contact medium."
    if column_name in {"street_name", "city", "region_code", "postal_code", "country_code"}:
        return f"Synthetic address attribute for the {humanize_identifier(table_name)} record."
    if column_name in {"name", "model", "manufacturer", "charge_description", "resource_name", "event_reason"}:
        return f"Descriptive attribute for {humanize_identifier(table_name)}."
    if column_name in {"quantity", "session_minutes", "data_limit_gb", "voice_limit_min"}:
        return f"Measured quantity captured in {humanize_identifier(column_name)}."
    if column_name in {"price_chf", "total_amount_chf", "amount_chf"}:
        return "Synthetic monetary value expressed in Swiss francs."
    return f"Business attribute for {humanize_identifier(column_name)} on the {humanize_identifier(table_name)} record."


def default_dmf_config(table_name: str, primary_key: str) -> dict[str, Any]:
    pk_metric_name = primary_key.replace("_", "")
    return {
        "metrics": [
            {
                "name": "SNOWFLAKE.CORE.ROW_COUNT",
                "arguments": [],
                "expectations": [
                    {
                        "name": f"{table_name}_has_rows",
                        "expression": "VALUE > 0",
                    }
                ],
            },
            {
                "name": "SNOWFLAKE.CORE.NULL_COUNT",
                "arguments": [primary_key],
                "expectations": [
                    {
                        "name": f"{pk_metric_name}_not_null",
                        "expression": "VALUE = 0",
                    }
                ],
            },
            {
                "name": "SNOWFLAKE.CORE.DUPLICATE_COUNT",
                "arguments": [primary_key],
                "expectations": [
                    {
                        "name": f"{pk_metric_name}_unique",
                        "expression": "VALUE = 0",
                    }
                ],
            },
        ]
    }


def complete_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    completed = deepcopy(manifest)
    tag_definitions = completed.setdefault("tag_definitions", {})
    tables_cfg = completed.setdefault("tables", {})

    if "source_entity" in tag_definitions:
        tag_definitions["source_entity"]["allowed_values"] = sorted(TABLE_SPECS)

    for table_name, spec in TABLE_SPECS.items():
        table_cfg = tables_cfg.setdefault(table_name, {})
        table_cfg.setdefault("comment", spec.description)
        table_cfg.setdefault(
            "tags",
            {
                "source_entity": table_name,
                "record_grain": infer_record_grain(table_name),
            },
        )

        primary_key = infer_primary_key_column(table_name, spec)
        if "dmf" not in table_cfg:
            table_cfg["dmf"] = default_dmf_config(table_name, primary_key)

        columns_cfg = table_cfg.setdefault("columns", {})
        for column in spec.columns:
            column_cfg = columns_cfg.setdefault(column.name, {})
            column_cfg.setdefault(
                "comment",
                default_column_comment(table_name, column.name, primary_key),
            )
            tags = column_cfg.setdefault("tags", {})
            tags.setdefault("semantic_type", infer_semantic_type(column.name))
            tags.setdefault("sensitivity", infer_sensitivity(column.name))
            tags.setdefault("identifier_role", infer_identifier_role(column.name, primary_key))

    return completed


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
