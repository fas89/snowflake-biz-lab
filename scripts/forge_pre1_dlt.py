"""Pre-1 ingestion: dlt pipeline that copies billing tables from the
telco_source Postgres database into the Snowflake bronze landing schema.

Designed to be run from the host (not the dbt-runner container) so it can use
the dedicated `.venv.pre1-dlt` virtualenv (created by `task pre1:bootstrap:dlt`).

Defaults assume the standard lab compose stack: Postgres reachable on
localhost:5433 with user/db `airflow` / `telco_source`, and Snowflake
credentials in the project `.env` (read via standard SNOWFLAKE_* names).

Outputs a receipt JSON at runtime/generated/pre1-dlt/receipt.json that
captures the source, target, row counts, dlt load_info, and timing — used by
downstream summary/observability tooling.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
RECEIPT_DIR = REPO_ROOT / "runtime" / "generated" / "pre1-dlt"

DEFAULT_TABLES = ["invoice", "invoice_charge"]


def _bridge_snowflake_env() -> None:
    """Re-export the lab's SNOWFLAKE_* vars into the names dlt's snowflake
    destination expects via its TOML/env-var config layer."""
    mapping = {
        "DESTINATION__SNOWFLAKE__CREDENTIALS__HOST": "SNOWFLAKE_ACCOUNT",
        "DESTINATION__SNOWFLAKE__CREDENTIALS__USERNAME": "SNOWFLAKE_USER",
        "DESTINATION__SNOWFLAKE__CREDENTIALS__DATABASE": "SNOWFLAKE_DATABASE",
        "DESTINATION__SNOWFLAKE__CREDENTIALS__WAREHOUSE": "SNOWFLAKE_WAREHOUSE",
        "DESTINATION__SNOWFLAKE__CREDENTIALS__ROLE": "SNOWFLAKE_ROLE",
    }
    for dlt_key, lab_key in mapping.items():
        if value := os.environ.get(lab_key):
            os.environ.setdefault(dlt_key, value)
    if pwd := os.environ.get("SNOWFLAKE_PASSWORD"):
        os.environ.setdefault("DESTINATION__SNOWFLAKE__CREDENTIALS__PASSWORD", pwd)
    if pk_path := os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH"):
        os.environ.setdefault(
            "DESTINATION__SNOWFLAKE__CREDENTIALS__PRIVATE_KEY",
            Path(pk_path).expanduser().read_text(),
        )
        if pp := os.environ.get("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE"):
            os.environ.setdefault(
                "DESTINATION__SNOWFLAKE__CREDENTIALS__PRIVATE_KEY_PASSPHRASE",
                pp,
            )


def _build_pg_url(args: argparse.Namespace) -> str:
    from urllib.parse import quote_plus

    user = quote_plus(args.pg_user)
    password = quote_plus(args.pg_password)
    return (
        f"postgresql+psycopg2://{user}:{password}@{args.pg_host}:{args.pg_port}/{args.pg_database}"
    )


def _row_counts_from_postgres(args: argparse.Namespace) -> dict[str, int]:
    import psycopg2

    conn = psycopg2.connect(
        host=args.pg_host,
        port=args.pg_port,
        dbname=args.pg_database,
        user=args.pg_user,
        password=args.pg_password,
    )
    counts: dict[str, int] = {}
    try:
        with conn.cursor() as cursor:
            for table in args.tables:
                cursor.execute(
                    f'SELECT count(*) FROM "{args.pg_schema}"."{table}"'
                )
                counts[table] = int(cursor.fetchone()[0])
    finally:
        conn.close()
    return counts


def _write_receipt(receipt: dict[str, Any]) -> Path:
    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    receipt_path = RECEIPT_DIR / "receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, default=str), encoding="utf-8")
    return receipt_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Pre-1 dlt acquisition: copy billing tables from telco_source Postgres "
            "into the Snowflake bronze stage schema."
        )
    )
    parser.add_argument(
        "--pg-host",
        default=os.environ.get("PG_SOURCE_HOST_HOST", "localhost"),
        help="Postgres host as seen from this script (default localhost; the host-side mapping of the compose `postgres` service).",
    )
    parser.add_argument(
        "--pg-port",
        type=int,
        default=int(os.environ.get("LOCAL_POSTGRES_PORT", "5433")),
        help="Host-mapped Postgres port (default 5433 from LOCAL_POSTGRES_PORT).",
    )
    parser.add_argument(
        "--pg-database",
        default=os.environ.get("PG_SOURCE_DATABASE", "telco_source"),
    )
    parser.add_argument(
        "--pg-schema",
        default=os.environ.get("PG_SOURCE_SCHEMA", "telco"),
    )
    parser.add_argument(
        "--pg-user",
        default=os.environ.get("PG_SOURCE_USER", os.environ.get("POSTGRES_USER", "airflow")),
    )
    parser.add_argument(
        "--pg-password",
        default=os.environ.get("PG_SOURCE_PASSWORD", os.environ.get("POSTGRES_PASSWORD", "airflow")),
    )
    parser.add_argument(
        "--tables",
        nargs="+",
        default=DEFAULT_TABLES,
        help=f"Postgres tables to ingest (default {DEFAULT_TABLES}).",
    )
    parser.add_argument(
        "--snowflake-schema",
        default=os.environ.get("SNOWFLAKE_STAGE_SCHEMA", "TELCO_STAGE_LOAD"),
        help="Target Snowflake schema (default SNOWFLAKE_STAGE_SCHEMA).",
    )
    parser.add_argument(
        "--write-disposition",
        default="replace",
        choices=["replace", "append", "merge"],
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned source/target without invoking dlt.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    started = datetime.now(timezone.utc)

    plan = {
        "source": {
            "kind": "postgres",
            "host": args.pg_host,
            "port": args.pg_port,
            "database": args.pg_database,
            "schema": args.pg_schema,
            "tables": args.tables,
        },
        "target": {
            "kind": "snowflake",
            "database": os.environ.get("SNOWFLAKE_DATABASE", "<unset>"),
            "schema": args.snowflake_schema,
            "tables": [t.upper() for t in args.tables],
        },
        "write_disposition": args.write_disposition,
    }

    if args.dry_run:
        print(json.dumps({"scenario": "pre-1", "engine": "dlt", "plan": plan}, indent=2))
        return 0

    _bridge_snowflake_env()

    try:
        import dlt
        from dlt.sources.sql_database import sql_database
    except ImportError as exc:
        print(
            "dlt is not installed. Bootstrap the pre-1 venv first: `task pre1:bootstrap:dlt`",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc

    pg_url = _build_pg_url(args)
    source = sql_database(credentials=pg_url, schema=args.pg_schema, table_names=args.tables)

    pipeline = dlt.pipeline(
        pipeline_name="telco_pre1_billing_dlt",
        destination="snowflake",
        dataset_name=args.snowflake_schema,
        progress="log",
    )

    load_info = pipeline.run(source, write_disposition=args.write_disposition)

    finished = datetime.now(timezone.utc)
    try:
        source_counts = _row_counts_from_postgres(args)
    except Exception:
        source_counts = {"error": traceback.format_exc().splitlines()[-1]}

    receipt = {
        "scenario": "pre-1",
        "engine": "dlt",
        "engine_version": getattr(dlt, "__version__", "unknown"),
        "pipeline_name": pipeline.pipeline_name,
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "duration_seconds": (finished - started).total_seconds(),
        "source_row_counts": source_counts,
        "load_info": str(load_info),
        **plan,
    }
    receipt_path = _write_receipt(receipt)
    print(f"Wrote pre-1 receipt to {receipt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
