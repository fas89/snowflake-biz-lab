"""Pre-2 ingestion: PyAirbyte pipeline that copies the party-domain tables
from the telco_source Postgres database into the Snowflake bronze landing
schema using the airbyte source-postgres + SnowflakeCache destination.

Designed to be run from the host (not the dbt-runner container) using the
dedicated `.venv.pre2-airbyte` virtualenv (created by `task pre2:bootstrap:airbyte`).

PyAirbyte will lazily install the source-postgres connector on first run
(install_if_missing=True). Connectors are installed as Python packages where
possible, falling back to Docker images otherwise.

Outputs a receipt JSON at runtime/generated/pre2-airbyte/receipt.json with
source/target metadata, per-stream record counts, and timing.
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
RECEIPT_DIR = REPO_ROOT / "runtime" / "generated" / "pre2-airbyte"

DEFAULT_TABLES = ["party", "account", "service", "subscription", "product_offering"]


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


def _build_snowflake_cache(args: argparse.Namespace):
    import airbyte as ab

    kwargs: dict[str, Any] = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "username": os.environ["SNOWFLAKE_USER"],
        "database": os.environ["SNOWFLAKE_DATABASE"],
        "schema_name": args.snowflake_schema,
        "warehouse": os.environ.get("SNOWFLAKE_WAREHOUSE"),
        "role": os.environ.get("SNOWFLAKE_ROLE"),
    }
    if pwd := os.environ.get("SNOWFLAKE_PASSWORD"):
        kwargs["password"] = pwd
    return ab.caches.SnowflakeCache(**{k: v for k, v in kwargs.items() if v is not None})


def _write_receipt(receipt: dict[str, Any]) -> Path:
    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    receipt_path = RECEIPT_DIR / "receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, default=str), encoding="utf-8")
    return receipt_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Pre-2 PyAirbyte acquisition: copy party-domain tables from telco_source "
            "Postgres into the Snowflake bronze stage schema."
        )
    )
    parser.add_argument(
        "--pg-host",
        default=os.environ.get("PG_SOURCE_HOST_HOST", "localhost"),
    )
    parser.add_argument(
        "--pg-port",
        type=int,
        default=int(os.environ.get("LOCAL_POSTGRES_PORT", "5433")),
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
    )
    parser.add_argument(
        "--snowflake-schema",
        default=os.environ.get("SNOWFLAKE_STAGE_SCHEMA", "TELCO_STAGE_LOAD"),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned source/target without invoking PyAirbyte.",
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
    }

    if args.dry_run:
        print(json.dumps({"scenario": "pre-2", "engine": "airbyte", "plan": plan}, indent=2))
        return 0

    try:
        import airbyte as ab
    except ImportError as exc:
        print(
            "PyAirbyte is not installed. Bootstrap the pre-2 venv first: `task pre2:bootstrap:airbyte`",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc

    source = ab.get_source(
        "source-postgres",
        config={
            "host": args.pg_host,
            "port": args.pg_port,
            "database": args.pg_database,
            "username": args.pg_user,
            "password": args.pg_password,
            "schemas": [args.pg_schema],
            "ssl_mode": {"mode": "disable"},
            "replication_method": {"method": "Standard"},
        },
        install_if_missing=True,
    )
    source.check()

    qualified_streams = [f"{args.pg_schema}.{t}" for t in args.tables]
    available = set(source.get_available_streams())
    selected = [s for s in qualified_streams if s in available]
    if not selected:
        selected = [t for t in args.tables if t in available]
    source.select_streams(selected)

    cache = _build_snowflake_cache(args)
    result = source.read(cache=cache)

    finished = datetime.now(timezone.utc)
    try:
        source_counts = _row_counts_from_postgres(args)
    except Exception:
        source_counts = {"error": traceback.format_exc().splitlines()[-1]}

    stream_counts: dict[str, int] = {}
    for stream_name in selected:
        try:
            stream_counts[stream_name] = sum(1 for _ in result[stream_name])
        except Exception:
            stream_counts[stream_name] = -1

    receipt = {
        "scenario": "pre-2",
        "engine": "airbyte",
        "engine_version": getattr(ab, "__version__", "unknown"),
        "selected_streams": selected,
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "duration_seconds": (finished - started).total_seconds(),
        "source_row_counts": source_counts,
        "stream_record_counts": stream_counts,
        **plan,
    }
    receipt_path = _write_receipt(receipt)
    print(f"Wrote pre-2 receipt to {receipt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
