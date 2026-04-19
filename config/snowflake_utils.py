from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def get_env(name: str, default: str | None = None, *, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value or ""


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def canonical_ident(identifier: str) -> str:
    return identifier.strip().upper()


def quote_ident(identifier: str) -> str:
    canonical = canonical_ident(identifier)
    return f'"{canonical.replace(chr(34), chr(34) * 2)}"'


def fq_name(*parts: str) -> str:
    return ".".join(quote_ident(part) for part in parts if part)


def sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_connection_kwargs() -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "account": get_env("SNOWFLAKE_ACCOUNT", required=True),
        "user": get_env("SNOWFLAKE_USER", required=True),
        "warehouse": get_env("SNOWFLAKE_WAREHOUSE", required=True),
        "database": get_env("SNOWFLAKE_DATABASE", required=True),
        "role": get_env("SNOWFLAKE_ROLE"),
        "session_parameters": {"QUERY_TAG": "snowflake-telco-lab"},
        "client_session_keep_alive": False,
    }

    oauth_token = get_env("SNOWFLAKE_OAUTH_TOKEN")
    private_key_path = get_env("SNOWFLAKE_PRIVATE_KEY_PATH")
    password = get_env("SNOWFLAKE_PASSWORD")
    authenticator = get_env("SNOWFLAKE_AUTHENTICATOR")

    if oauth_token:
        kwargs["authenticator"] = "oauth"
        kwargs["token"] = oauth_token
    elif private_key_path:
        from cryptography.hazmat.primitives import serialization

        passphrase = get_env("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")
        key_bytes = Path(private_key_path).expanduser().read_bytes()
        p_key = serialization.load_pem_private_key(
            key_bytes,
            password=passphrase.encode() if passphrase else None,
        )
        kwargs["private_key"] = p_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    elif password:
        kwargs["password"] = password
        if authenticator:
            kwargs["authenticator"] = authenticator
    elif authenticator:
        kwargs["authenticator"] = authenticator
    else:
        raise RuntimeError(
            "Provide one of SNOWFLAKE_OAUTH_TOKEN, SNOWFLAKE_PRIVATE_KEY_PATH, "
            "SNOWFLAKE_PASSWORD, or SNOWFLAKE_AUTHENTICATOR."
        )

    return {key: value for key, value in kwargs.items() if value not in (None, "")}


def get_connection() -> Any:
    import snowflake.connector

    return snowflake.connector.connect(**build_connection_kwargs())


def execute_many(cursor: Any, statements: list[str]) -> None:
    for statement in statements:
        sql = statement.strip()
        if not sql:
            continue
        cursor.execute(sql)


def fetch_all_dicts(cursor: Any, query: str) -> list[dict[str, Any]]:
    cursor.execute(query)
    columns = [desc[0].lower() for desc in cursor.description]
    rows = cursor.fetchall()
    return [dict(zip(columns, row)) for row in rows]
