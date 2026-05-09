from __future__ import annotations

import os
from typing import Any


SF_TO_PG_TYPE: dict[str, str] = {
    "VARCHAR": "TEXT",
    "TEXT": "TEXT",
    "STRING": "TEXT",
    "DATE": "DATE",
    "TIMESTAMP_NTZ": "TIMESTAMP",
    "TIMESTAMP": "TIMESTAMP",
    "TIMESTAMPTZ": "TIMESTAMPTZ",
    "BOOLEAN": "BOOLEAN",
    "NUMBER": "BIGINT",
}


def get_env(name: str, default: str | None = None, *, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value or ""


def quote_ident(identifier: str) -> str:
    raw = identifier.strip()
    return f'"{raw.replace(chr(34), chr(34) * 2)}"'


def fq_name(*parts: str) -> str:
    return ".".join(quote_ident(part) for part in parts if part)


def snowflake_type_to_postgres(snowflake_type: str) -> str:
    raw = snowflake_type.strip().upper()
    if raw.startswith("NUMBER(") and raw.endswith(")"):
        return "NUMERIC" + raw[len("NUMBER"):]
    if raw.startswith("VARCHAR(") and raw.endswith(")"):
        return "TEXT"
    return SF_TO_PG_TYPE.get(raw, "TEXT")


def build_connection_kwargs() -> dict[str, Any]:
    return {
        "host": get_env("PG_SOURCE_HOST", "postgres"),
        "port": int(get_env("PG_SOURCE_PORT", "5432")),
        "dbname": get_env("PG_SOURCE_DATABASE", "telco_source"),
        "user": get_env("PG_SOURCE_USER", get_env("POSTGRES_USER", "airflow")),
        "password": get_env("PG_SOURCE_PASSWORD", get_env("POSTGRES_PASSWORD", "airflow")),
    }


def get_connection() -> Any:
    import psycopg2

    return psycopg2.connect(**build_connection_kwargs())


def source_schema() -> str:
    return get_env("PG_SOURCE_SCHEMA", "telco")
