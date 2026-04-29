#!/usr/bin/env python3
"""MCP-forge the B2 generated-assets scenario from seeded Snowflake metadata.

B2 starts with the forge-cli MCP server, not a replay fixture. The MCP
``forge_from_source`` tool reads the lab's seeded Snowflake schema, emits the raw
logical model + contract, and writes a local receipt. The lab then applies a
deterministic B2 envelope and runs the normal generators so the product owns its
dbt project, Airflow DAG, and Jenkinsfile inside the workspace.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from local_env_utils import parse_env_file


LAB_REPO = Path(__file__).resolve().parents[1]
WORKSPACE = LAB_REPO / "gitlab" / "path-b-ai-telco-silver-import-demo"
PRODUCT_DIR = (
    WORKSPACE / "variants" / "B2-ai-generate-in-workspace" / "subscriber360-generated"
)
DEFAULT_FLUID = LAB_REPO / ".venv.fluid-dev" / "bin" / "fluid"
DEFAULT_SECRETS = LAB_REPO / "runtime" / "generated" / "fluid.local.env"

PRODUCT_ID = "silver.telco.subscriber360_ai_generated_v1"
PRODUCT_NAME = "Telco Subscriber 360 (MCP Generated Assets)"
PRODUCT_DESCRIPTION = (
    "MCP-forged silver Subscriber 360 product over the seeded Snowflake telco "
    "schema. B2 reads live Snowflake metadata through forge-cli MCP, then "
    "generates the dbt project, Airflow DAG, and Jenkins CI inside this product "
    "workspace."
)
BUILD_ID = "ai_subscriber360_generated_build"
DBT_REPO = "./generated/dbt/dbt_dv2_subscriber360"
MCP_MODEL_NAME = "telco_subscriber360_mcp_generated"
MCP_CREDENTIAL_ID = "snowflake-lab-env"

SEEDED_TABLES = [
    "PARTY",
    "ACCOUNT",
    "PRODUCT_OFFERING",
    "SERVICE",
    "SUBSCRIPTION",
    "RESOURCE",
    "USAGE_EVENT",
    "CUSTOMER_INTERACTION",
    "TROUBLE_TICKET",
    "INVOICE",
    "INVOICE_CHARGE",
]

SOURCE_IDENTIFIER_BY_EXPOSE = {
    "account_source": "ACCOUNT",
    "service_source": "SERVICE",
    "subscription_source": "SUBSCRIPTION",
    "product_offering_source": "PRODUCT_OFFERING",
    "usage_event_source": "USAGE_EVENT",
    "invoice_charge_source": "INVOICE_CHARGE",
    "invoice_source": "INVOICE",
    "customer_interaction_source": "CUSTOMER_INTERACTION",
    "trouble_ticket_source": "TROUBLE_TICKET",
}

BRONZE_CONSUMES: list[dict[str, str]] = [
    {
        "productId": "bronze.telco.party_v1",
        "exposeId": "account_source",
        "purpose": "Account and billing relationship grain for Subscriber 360.",
    },
    {
        "productId": "bronze.telco.party_v1",
        "exposeId": "service_source",
        "purpose": "Operational service status and activation history.",
    },
    {
        "productId": "bronze.telco.party_v1",
        "exposeId": "subscription_source",
        "purpose": "Commercial plan and renewal relationships for each service.",
    },
    {
        "productId": "bronze.telco.party_v1",
        "exposeId": "product_offering_source",
        "purpose": "Product plan names, categories, and recurring pricing.",
    },
    {
        "productId": "bronze.telco.usage_v1",
        "exposeId": "usage_event_source",
        "purpose": "Recent usage intensity and service activity.",
    },
    {
        "productId": "bronze.telco.billing_v1",
        "exposeId": "invoice_charge_source",
        "purpose": "Charge and recurring revenue signals for support prioritization.",
    },
    {
        "productId": "bronze.telco.billing_v1",
        "exposeId": "invoice_source",
        "purpose": "Invoice-to-account relationship required for charge attribution.",
    },
    {
        "productId": "bronze.telco.usage_v1",
        "exposeId": "customer_interaction_source",
        "purpose": "Recent engagement and support contact history.",
    },
    {
        "productId": "bronze.telco.usage_v1",
        "exposeId": "trouble_ticket_source",
        "purpose": "Open ticket posture and severity indicators.",
    },
]

CORE_SCHEMA: list[dict[str, Any]] = [
    {"name": "PARTY_ID", "type": "STRING", "required": True},
    {"name": "ACCOUNT_ID", "type": "STRING", "required": True},
    {"name": "ACCOUNT_NUMBER", "type": "STRING", "required": True},
    {"name": "SERVICE_ID", "type": "STRING", "required": True},
    {"name": "SUBSCRIPTION_ID", "type": "STRING"},
    {"name": "PRODUCT_OFFERING_NAME", "type": "STRING"},
    {"name": "SERVICE_STATUS", "type": "STRING", "required": True},
    {"name": "BILLING_STATUS", "type": "STRING", "required": True},
    {"name": "MONTHLY_RECURRING_CHARGE", "type": "NUMBER", "required": True},
    {"name": "DATA_MB_30D", "type": "NUMBER", "required": True},
    {"name": "INTERACTION_COUNT_30D", "type": "INTEGER", "required": True},
    {"name": "OPEN_TICKET_COUNT_30D", "type": "INTEGER", "required": True},
    {"name": "SUPPORT_HEALTH_SCORE", "type": "NUMBER", "required": True},
    {"name": "SUPPORT_RISK_BAND", "type": "STRING", "required": True},
    {"name": "LAST_INTERACTION_AT", "type": "TIMESTAMP"},
    {"name": "SNAPSHOT_AT", "type": "TIMESTAMP", "required": True},
]

SCORECARD_SCHEMA: list[dict[str, Any]] = [
    {"name": "ACCOUNT_ID", "type": "STRING", "required": True},
    {"name": "SERVICE_ID", "type": "STRING", "required": True},
    {"name": "USAGE_EVENTS_30D", "type": "INTEGER", "required": True},
    {"name": "DATA_MB_30D", "type": "NUMBER", "required": True},
    {"name": "INTERACTION_COUNT_30D", "type": "INTEGER", "required": True},
    {"name": "OPEN_TICKET_COUNT_30D", "type": "INTEGER", "required": True},
    {"name": "TICKET_SEVERITY_INDEX", "type": "NUMBER", "required": True},
    {"name": "TOTAL_CHARGES_30D", "type": "NUMBER", "required": True},
    {"name": "MONTHLY_RECURRING_CHARGE", "type": "NUMBER", "required": True},
    {"name": "SUPPORT_HEALTH_SCORE", "type": "NUMBER", "required": True},
    {"name": "SUPPORT_RISK_BAND", "type": "STRING", "required": True},
    {"name": "SNAPSHOT_AT", "type": "TIMESTAMP", "required": True},
]


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def _merge_env(secrets_file: Path) -> dict[str, str]:
    merged = dict(os.environ)
    for env_file in (LAB_REPO / ".env", secrets_file):
        merged.update({k: v for k, v in parse_env_file(env_file).items() if v})
    return merged


def _run(
    cmd: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    display_cmd: list[str] | None = None,
) -> None:
    print("+ " + " ".join(display_cmd or cmd))
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def _clean_generated_product(product_dir: Path) -> None:
    for name in ("contract.fluid.yaml", "Jenkinsfile", "generated", "runtime"):
        path = product_dir / name
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


class McpClient:
    def __init__(self, cmd: list[str], *, cwd: Path, env: dict[str, str]) -> None:
        self._next_id = 1
        self._proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        if self._proc.stdin is None or self._proc.stdout is None:
            raise RuntimeError("Could not open MCP stdio pipes")

    def close(self) -> None:
        try:
            if self._proc.stdin:
                self._proc.stdin.close()
        except Exception:
            pass
        try:
            self._proc.terminate()
        except Exception:
            pass
        try:
            self._proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._proc.kill()

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {},
        }
        assert self._proc.stdin is not None
        assert self._proc.stdout is not None
        self._proc.stdin.write(json.dumps(payload) + "\n")
        self._proc.stdin.flush()
        while True:
            line = self._proc.stdout.readline()
            if not line:
                stderr = ""
                if self._proc.stderr is not None:
                    stderr = self._proc.stderr.read()
                raise RuntimeError(f"MCP server exited before response: {stderr.strip()}")
            try:
                response = json.loads(line)
            except json.JSONDecodeError:
                continue
            if response.get("id") != request_id:
                continue
            if response.get("error"):
                raise RuntimeError(response["error"])
            return dict(response.get("result") or {})


def _tool_text(result: dict[str, Any]) -> dict[str, Any]:
    content = result.get("content") or []
    if not content:
        return {}
    text = content[0].get("text") if isinstance(content[0], dict) else None
    if not isinstance(text, str):
        return {}
    return json.loads(text)


def _run_mcp_forge(
    *,
    fluid: Path,
    product_dir: Path,
    env: dict[str, str],
    credential_id: str,
) -> tuple[Path, dict[str, Any]]:
    raw_dir = product_dir / "runtime" / "generated" / "mcp-forge" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_path = raw_dir / "contract.fluid.yaml"
    logical_path = raw_dir / "contract.fluid.yaml.model.json"

    for required in (
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_USER",
        "SNOWFLAKE_DATABASE",
        "SNOWFLAKE_STAGE_SCHEMA",
    ):
        if not env.get(required):
            raise RuntimeError(f"{required} is required for B2 MCP Snowflake forge")

    cmd = [
        str(fluid),
        "mcp",
        "serve",
        "--allow-tools",
        "list_source_tables,forge_from_source",
        "--readable-paths",
        str(product_dir),
        "--writable-paths",
        str(product_dir),
    ]
    print("+ " + " ".join(cmd))
    client = McpClient(cmd, cwd=product_dir, env=env)
    try:
        init = client.request(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "clientInfo": {"name": "snowflake-biz-lab-b2", "version": "1"},
            },
        )
        base_args = {
            "source": "snowflake",
            "credentials": {"credential_id": credential_id},
            "scope": {
                "database": env["SNOWFLAKE_DATABASE"],
                "schema": env["SNOWFLAKE_STAGE_SCHEMA"],
                "tables": SEEDED_TABLES,
            },
            "allow_metadata_service": False,
        }
        table_result = _tool_text(
            client.request(
                "tools/call",
                {"name": "list_source_tables", "arguments": base_args},
            )
        )
        forge_args = dict(base_args)
        forge_args.update(
            {
                "technique": "data_vault_2",
                "engine": "dbt",
                "name": MCP_MODEL_NAME,
                "output_path": str(output_path),
                "logical_path": str(logical_path),
            }
        )
        forge_result = _tool_text(
            client.request(
                "tools/call",
                {"name": "forge_from_source", "arguments": forge_args},
            )
        )
    finally:
        client.close()

    if not output_path.exists() or not logical_path.exists():
        raise FileNotFoundError("MCP forge did not write the raw contract/model sidecar")

    receipt = {
        "kind": "B2McpForgeReceipt",
        "server": init.get("serverInfo", {}).get("name", "forge-cli-mcp"),
        "protocolVersion": init.get("protocolVersion"),
        "source": "snowflake",
        "credential_id": credential_id,
        "scope": {
            "database": env["SNOWFLAKE_DATABASE"],
            "schema": env["SNOWFLAKE_STAGE_SCHEMA"],
            "tables": SEEDED_TABLES,
        },
        "table_count": len(table_result.get("tables") or []),
        "table_names": [t.get("name") for t in table_result.get("tables") or []],
        "raw_contract": str(output_path.relative_to(product_dir)),
        "raw_model": str(logical_path.relative_to(product_dir)),
        "validation": forge_result.get("validation"),
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    receipt_path = product_dir / "runtime" / "generated" / "mcp-forge" / "receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return raw_dir, receipt


def _semantics_core() -> dict[str, Any]:
    return {
        "name": "subscriber360_core_semantic_model",
        "description": "Business semantic layer for the MCP-generated subscriber view.",
        "defaultAggTimeDimension": "SNAPSHOT_AT",
        "entities": [
            {"name": "ACCOUNT_ID", "type": "primary"},
            {"name": "SERVICE_ID", "type": "unique"},
            {"name": "SUBSCRIPTION_ID", "type": "foreign"},
        ],
        "measures": [
            {"name": "MONTHLY_RECURRING_CHARGE", "agg": "sum", "createMetric": True},
            {"name": "DATA_MB_30D", "agg": "sum", "createMetric": True},
            {"name": "SUPPORT_HEALTH_SCORE", "agg": "avg"},
        ],
        "dimensions": [
            {"name": "SERVICE_STATUS", "type": "categorical"},
            {"name": "BILLING_STATUS", "type": "categorical"},
            {"name": "SUPPORT_RISK_BAND", "type": "categorical"},
            {
                "name": "SNAPSHOT_AT",
                "type": "time",
                "typeParams": {"timeGranularity": "day"},
            },
        ],
        "metrics": [
            {
                "name": "active_recurring_revenue",
                "type": "simple",
                "measure": "MONTHLY_RECURRING_CHARGE",
                "filter": "SERVICE_STATUS = 'active'",
                "owner": "telco-ai-product",
            },
            {
                "name": "avg_support_health_score",
                "type": "simple",
                "measure": "SUPPORT_HEALTH_SCORE",
                "owner": "telco-ai-product",
            },
        ],
    }


def _semantics_scorecard() -> dict[str, Any]:
    return {
        "name": "subscriber_health_scorecard_semantic_model",
        "description": "KPI layer for service support intensity and subscriber health.",
        "defaultAggTimeDimension": "SNAPSHOT_AT",
        "entities": [
            {"name": "ACCOUNT_ID", "type": "primary"},
            {"name": "SERVICE_ID", "type": "unique"},
        ],
        "measures": [
            {"name": "OPEN_TICKET_COUNT_30D", "agg": "sum", "createMetric": True},
            {"name": "INTERACTION_COUNT_30D", "agg": "sum", "createMetric": True},
            {"name": "SUPPORT_HEALTH_SCORE", "agg": "avg", "createMetric": True},
        ],
        "dimensions": [
            {"name": "SUPPORT_RISK_BAND", "type": "categorical"},
            {
                "name": "SNAPSHOT_AT",
                "type": "time",
                "typeParams": {"timeGranularity": "day"},
            },
        ],
        "metrics": [
            {
                "name": "average_support_health",
                "type": "simple",
                "measure": "SUPPORT_HEALTH_SCORE",
                "owner": "telco-ai-product",
            },
            {
                "name": "open_ticket_pressure",
                "type": "simple",
                "measure": "OPEN_TICKET_COUNT_30D",
                "owner": "telco-ai-product",
            },
        ],
    }


def _expose(
    *,
    expose_id: str,
    title: str,
    description: str,
    table: str,
    schema: list[dict[str, Any]],
    semantics: dict[str, Any],
) -> dict[str, Any]:
    return {
        "exposeId": expose_id,
        "title": title,
        "description": description,
        "version": "1.0.0",
        "kind": "table",
        "binding": {
            "platform": "snowflake",
            "format": "snowflake_table",
            "location": {
                "account": "{{ env.SNOWFLAKE_ACCOUNT }}",
                "database": "{{ env.SNOWFLAKE_DATABASE }}",
                "schema": "{{ env.SNOWFLAKE_FLUID_SCHEMA }}",
                "table": table,
            },
        },
        "contract": {"schema": schema},
        "qos": {"availability": "99.5%", "freshnessSLO": "PT6H"},
        "semantics": semantics,
    }


def _build_final_contract(raw_dir: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    product_dir = raw_dir.parents[3]
    raw_contract = raw_dir / "contract.fluid.yaml"
    raw_model = raw_dir / "contract.fluid.yaml.model.json"
    return {
        "fluidVersion": "0.7.2",
        "kind": "DataProduct",
        "id": PRODUCT_ID,
        "name": PRODUCT_NAME,
        "description": PRODUCT_DESCRIPTION,
        "domain": "telco",
        "labels": {
            "b2McpSeededSnowflake": "true",
            "b2McpServer": str(receipt.get("server") or "forge-cli-mcp"),
            "b2McpSource": "snowflake",
            "b2McpModel": "runtime/generated/mcp-forge/raw/contract.fluid.yaml.model.json",
            "b2McpRawContract": "runtime/generated/mcp-forge/raw/contract.fluid.yaml",
            "b2McpReceipt": "runtime/generated/mcp-forge/receipt.json",
            "b2GeneratedAssets": "dbt-airflow-jenkins",
            "modelSidecar": str(raw_model.relative_to(product_dir)),
        },
        "metadata": {
            "layer": "Silver",
            "owner": {"team": "telco-ai-product", "email": "ai-product@example.com"},
            "provenance": {
                "source": "mcp-forge_from_source",
                "catalog": "snowflake",
                "scope": receipt.get("scope"),
                "rawContract": str(raw_contract.relative_to(product_dir)),
                "rawModel": str(raw_model.relative_to(product_dir)),
                "labHardening": "deterministic-b2-generated-assets-and-bronze-lineage",
            },
        },
        "consumes": BRONZE_CONSUMES,
        "builds": [
            {
                "id": BUILD_ID,
                "description": (
                    "Build the MCP-forged Subscriber 360 marts from the generated "
                    f"in-product dbt project at {DBT_REPO}."
                ),
                "pattern": "hybrid-reference",
                "engine": "dbt",
                "repository": DBT_REPO,
                "properties": {
                    "model": "subscriber_health_scorecard",
                    "vars": {
                        "stage_schema": "{{ env.SNOWFLAKE_STAGE_SCHEMA }}",
                        "marts_schema": "{{ env.SNOWFLAKE_FLUID_SCHEMA }}",
                        "enforce_semantics": True,
                    },
                },
                "execution": {
                    "trigger": {"type": "schedule", "cron": "15 6 * * *"},
                    "runtime": {
                        "platform": "snowflake",
                        "resources": {
                            "warehouse": "{{ env.SNOWFLAKE_WAREHOUSE }}",
                            "database": "{{ env.SNOWFLAKE_DATABASE }}",
                            "schema": "{{ env.SNOWFLAKE_FLUID_SCHEMA }}",
                            "role": "{{ env.SNOWFLAKE_ROLE }}",
                        },
                    },
                    "retries": {"count": 2, "delaySeconds": 120, "backoff": "exponential"},
                },
                "outputs": ["subscriber_health_scorecard"],
            }
        ],
        "exposes": [
            _expose(
                expose_id="subscriber360_core",
                title="Subscriber 360 Core (MCP Generated)",
                description=(
                    "Subscriber, service, plan, usage, billing, and support health "
                    "signals generated into the B2 workspace from seeded Snowflake metadata."
                ),
                table="SUBSCRIBER360_CORE_V1",
                schema=CORE_SCHEMA,
                semantics=_semantics_core(),
            ),
            _expose(
                expose_id="subscriber_health_scorecard",
                title="Subscriber Health Scorecard (MCP Generated)",
                description=(
                    "Service-level health scorecard generated into the B2 workspace "
                    "from MCP-discovered Snowflake telco tables."
                ),
                table="SUBSCRIBER_HEALTH_SCORECARD_V1",
                schema=SCORECARD_SCHEMA,
                semantics=_semantics_scorecard(),
            ),
        ],
    }


def _write_sources_yml(dbt_dir: Path) -> None:
    tables = [
        {
            "name": expose_id,
            "identifier": identifier,
            "description": f"Seeded Snowflake table {identifier} discovered through MCP.",
        }
        for expose_id, identifier in SOURCE_IDENTIFIER_BY_EXPOSE.items()
    ]
    payload = {
        "version": 2,
        "sources": [
            {
                "name": "raw",
                "description": "MCP-discovered seeded Snowflake telco tables",
                "database": "{{ env_var('SNOWFLAKE_DATABASE') }}",
                "schema": "{{ env_var('SNOWFLAKE_STAGE_SCHEMA', 'PUBLIC') }}",
                "tables": tables,
            }
        ],
    }
    _write_yaml(dbt_dir / "models" / "sources.yml", payload)


def _write_staging_models(dbt_dir: Path) -> None:
    staging = dbt_dir / "models" / "staging"
    staging.mkdir(parents=True, exist_ok=True)
    for expose_id in SOURCE_IDENTIFIER_BY_EXPOSE:
        model_name = f"stg_{expose_id}"
        sql = (
            "-- Generated by the B2 MCP lab flow.\n"
            "{{ config(materialized='view') }}\n\n"
            "select *\n"
            f"from {{{{ source('raw', '{expose_id}') }}}}\n"
        )
        (staging / f"{model_name}.sql").write_text(sql, encoding="utf-8")


MART_CORE_SQL = """-- Generated by the B2 MCP lab flow.
{{ config(alias='SUBSCRIBER360_CORE_V1', materialized='table') }}

with usage_30d as (
  select
    account_id,
    service_id,
    count(*) as usage_events_30d,
    round(sum(case when usage_type = 'data_mb' then quantity else 0 end), 2) as data_mb_30d
  from {{ ref('stg_usage_event_source') }}
  where event_timestamp >= dateadd(day, -30, current_timestamp())
  group by account_id, service_id
),
interactions_30d as (
  select
    account_id,
    service_id,
    count(*) as interaction_count_30d,
    max(interaction_timestamp) as last_interaction_at
  from {{ ref('stg_customer_interaction_source') }}
  where interaction_timestamp >= dateadd(day, -30, current_timestamp())
  group by account_id, service_id
),
tickets_30d as (
  select
    account_id,
    service_id,
    count_if(status <> 'resolved') as open_ticket_count_30d,
    avg(case severity when 'critical' then 4 when 'high' then 3 when 'medium' then 2 else 1 end) as ticket_severity_index
  from {{ ref('stg_trouble_ticket_source') }}
  where opened_at >= dateadd(day, -30, current_timestamp())
  group by account_id, service_id
),
charges_30d as (
  select
    svc.account_id,
    svc.service_id,
    round(sum(ic.amount_chf), 2) as total_charges_30d,
    round(sum(case when ic.charge_type = 'recurring_charge' then ic.amount_chf else 0 end), 2) as monthly_recurring_charge
  from {{ ref('stg_invoice_charge_source') }} ic
  join {{ ref('stg_invoice_source') }} inv
    on ic.invoice_id = inv.invoice_id
  join {{ ref('stg_service_source') }} svc
    on inv.account_id = svc.account_id
  where ic.charge_date >= dateadd(day, -30, current_date())
  group by svc.account_id, svc.service_id
),
scored as (
  select
    s.account_id,
    s.service_id,
    coalesce(u.usage_events_30d, 0) as usage_events_30d,
    coalesce(u.data_mb_30d, 0) as data_mb_30d,
    coalesce(i.interaction_count_30d, 0) as interaction_count_30d,
    coalesce(t.open_ticket_count_30d, 0) as open_ticket_count_30d,
    coalesce(t.ticket_severity_index, 0) as ticket_severity_index,
    coalesce(c.total_charges_30d, 0) as total_charges_30d,
    coalesce(c.monthly_recurring_charge, 0) as monthly_recurring_charge,
    greatest(
      0,
      100
      - coalesce(t.open_ticket_count_30d, 0) * 15
      - coalesce(t.ticket_severity_index, 0) * 8
      - least(coalesce(i.interaction_count_30d, 0), 10) * 2
    ) as support_health_score,
    case
      when coalesce(t.open_ticket_count_30d, 0) >= 3 or coalesce(t.ticket_severity_index, 0) >= 3.5 then 'critical'
      when coalesce(t.open_ticket_count_30d, 0) >= 2 then 'high'
      when coalesce(i.interaction_count_30d, 0) >= 3 then 'watch'
      else 'healthy'
    end as support_risk_band,
    i.last_interaction_at,
    current_timestamp() as snapshot_at
  from {{ ref('stg_service_source') }} s
  left join usage_30d u
    on s.account_id = u.account_id and s.service_id = u.service_id
  left join interactions_30d i
    on s.account_id = i.account_id and s.service_id = i.service_id
  left join tickets_30d t
    on s.account_id = t.account_id and s.service_id = t.service_id
  left join charges_30d c
    on s.account_id = c.account_id and s.service_id = c.service_id
)
select
  a.party_id,
  a.account_id,
  a.account_number,
  s.service_id,
  sub.subscription_id,
  po.name as product_offering_name,
  s.status as service_status,
  a.status as billing_status,
  scored.monthly_recurring_charge,
  scored.data_mb_30d,
  scored.interaction_count_30d,
  scored.open_ticket_count_30d,
  scored.support_health_score,
  scored.support_risk_band,
  scored.last_interaction_at,
  scored.snapshot_at
from {{ ref('stg_account_source') }} a
join {{ ref('stg_service_source') }} s
  on a.account_id = s.account_id
left join {{ ref('stg_subscription_source') }} sub
  on s.service_id = sub.service_id
left join {{ ref('stg_product_offering_source') }} po
  on sub.product_offering_id = po.product_offering_id
left join scored
  on s.account_id = scored.account_id and s.service_id = scored.service_id
"""

MART_SCORECARD_SQL = """-- Generated by the B2 MCP lab flow.
{{ config(alias='SUBSCRIBER_HEALTH_SCORECARD_V1', materialized='table') }}

with core as (
  select *
  from {{ ref('subscriber360_core') }}
),
usage_30d as (
  select
    account_id,
    service_id,
    count(*) as usage_events_30d
  from {{ ref('stg_usage_event_source') }}
  where event_timestamp >= dateadd(day, -30, current_timestamp())
  group by account_id, service_id
),
tickets_30d as (
  select
    account_id,
    service_id,
    avg(case severity when 'critical' then 4 when 'high' then 3 when 'medium' then 2 else 1 end) as ticket_severity_index
  from {{ ref('stg_trouble_ticket_source') }}
  where opened_at >= dateadd(day, -30, current_timestamp())
  group by account_id, service_id
),
charges_30d as (
  select
    svc.account_id,
    svc.service_id,
    round(sum(ic.amount_chf), 2) as total_charges_30d
  from {{ ref('stg_invoice_charge_source') }} ic
  join {{ ref('stg_invoice_source') }} inv
    on ic.invoice_id = inv.invoice_id
  join {{ ref('stg_service_source') }} svc
    on inv.account_id = svc.account_id
  where ic.charge_date >= dateadd(day, -30, current_date())
  group by svc.account_id, svc.service_id
)
select
  core.account_id,
  core.service_id,
  coalesce(usage_30d.usage_events_30d, 0) as usage_events_30d,
  core.data_mb_30d,
  core.interaction_count_30d,
  core.open_ticket_count_30d,
  coalesce(tickets_30d.ticket_severity_index, 0) as ticket_severity_index,
  coalesce(charges_30d.total_charges_30d, 0) as total_charges_30d,
  core.monthly_recurring_charge,
  core.support_health_score,
  core.support_risk_band,
  core.snapshot_at
from core
left join usage_30d
  on core.account_id = usage_30d.account_id and core.service_id = usage_30d.service_id
left join tickets_30d
  on core.account_id = tickets_30d.account_id and core.service_id = tickets_30d.service_id
left join charges_30d
  on core.account_id = charges_30d.account_id and core.service_id = charges_30d.service_id
"""


def _write_marts(dbt_dir: Path) -> None:
    marts = dbt_dir / "models" / "marts"
    marts.mkdir(parents=True, exist_ok=True)
    (marts / "subscriber360_core.sql").write_text(MART_CORE_SQL, encoding="utf-8")
    (marts / "subscriber_health_scorecard.sql").write_text(
        MART_SCORECARD_SQL,
        encoding="utf-8",
    )
    schema = {
        "version": 2,
        "models": [
            {
                "name": "subscriber360_core",
                "description": "MCP-generated Subscriber 360 core mart.",
                "config": {"access": "public"},
                "columns": [{"name": item["name"]} for item in CORE_SCHEMA],
            },
            {
                "name": "subscriber_health_scorecard",
                "description": "MCP-generated Subscriber Health Scorecard mart.",
                "config": {"access": "public"},
                "columns": [{"name": item["name"]} for item in SCORECARD_SCHEMA],
            },
        ],
    }
    _write_yaml(marts / "schema.yml", schema)


def _harden_generated_dbt(dbt_dir: Path) -> None:
    _write_sources_yml(dbt_dir)
    _write_staging_models(dbt_dir)
    _write_marts(dbt_dir)


def _clean_dbt_parse_artifacts(dbt_dir: Path) -> None:
    for name in ("target", "logs", ".user.yml"):
        path = dbt_dir / name
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


def _write_summary(product_dir: Path, receipt: dict[str, Any]) -> None:
    summary = {
        "scenario": "B2-ai-generate-in-workspace",
        "mode": "mcp-snowflake-seeded",
        "server": receipt.get("server"),
        "source": "snowflake",
        "database": (receipt.get("scope") or {}).get("database"),
        "schema": (receipt.get("scope") or {}).get("schema"),
        "table_count": receipt.get("table_count"),
        "raw_contract": "runtime/generated/mcp-forge/raw/contract.fluid.yaml",
        "raw_model": "runtime/generated/mcp-forge/raw/contract.fluid.yaml.model.json",
        "receipt": "runtime/generated/mcp-forge/receipt.json",
        "final_contract": "contract.fluid.yaml",
        "generated_dbt": DBT_REPO,
        "generated_airflow": "./generated/airflow",
        "generated_ci": "Jenkinsfile",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    summary_path = product_dir / "runtime" / "generated" / "mcp-forge" / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fluid", type=Path, default=DEFAULT_FLUID, help="Path to fluid CLI.")
    parser.add_argument(
        "--product-dir",
        type=Path,
        default=PRODUCT_DIR,
        help="B2 product directory to write.",
    )
    parser.add_argument(
        "--secrets-file",
        type=Path,
        default=DEFAULT_SECRETS,
        help="Lab secrets env file.",
    )
    parser.add_argument(
        "--credential-id",
        default=MCP_CREDENTIAL_ID,
        help=(
            "MCP credential_id envelope. The lab default uses Snowflake env vars "
            "loaded into the MCP process; no raw secret is sent over MCP."
        ),
    )
    parser.add_argument(
        "--install-mode",
        default=None,
        choices=("pypi", "dev-source"),
        help="Jenkinsfile install mode. Defaults to JENKINS_INSTALL_MODE or dev-source.",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Do not remove existing generated B2 assets before forging.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fluid = args.fluid.expanduser().resolve()
    product_dir = args.product_dir.expanduser().resolve()
    secrets_file = args.secrets_file.expanduser().resolve()

    if not fluid.exists():
        print(f"fluid CLI not found: {fluid}", file=sys.stderr)
        return 1
    if not WORKSPACE.exists():
        print(f"workspace not found: {WORKSPACE}; run task workspaces:bootstrap", file=sys.stderr)
        return 1
    if not secrets_file.exists():
        print(f"secrets file not found: {secrets_file}; run task catalogs:bootstrap", file=sys.stderr)
        return 1

    product_dir.mkdir(parents=True, exist_ok=True)
    if not args.keep_existing:
        _clean_generated_product(product_dir)

    env = _merge_env(secrets_file)
    env["FLUID_SECRETS_FILE"] = str(secrets_file)
    env["FLUID_UPSTREAM_CONTRACTS"] = str(LAB_REPO / "fluid" / "contracts")
    env["PATH"] = f"{fluid.parent}:{env.get('PATH', '')}"
    env.pop("DBT_TARGET", None)

    raw_dir, receipt = _run_mcp_forge(
        fluid=fluid,
        product_dir=product_dir,
        env=env,
        credential_id=args.credential_id,
    )
    final_contract = _build_final_contract(raw_dir, receipt)
    _write_yaml(product_dir / "contract.fluid.yaml", final_contract)

    _run([str(fluid), "validate", "contract.fluid.yaml"], cwd=product_dir, env=env)
    dbt_dir = product_dir / "generated" / "dbt" / "dbt_dv2_subscriber360"
    _run(
        [
            str(fluid),
            "generate",
            "transformation",
            "contract.fluid.yaml",
            "-o",
            str(dbt_dir),
            "--overwrite",
        ],
        cwd=product_dir,
        env=env,
    )
    _harden_generated_dbt(dbt_dir)
    _run(["dbt", "parse", "--project-dir", str(dbt_dir), "--profiles-dir", str(dbt_dir)], cwd=product_dir, env=env)
    _clean_dbt_parse_artifacts(dbt_dir)
    _run(
        [
            str(fluid),
            "generate",
            "schedule",
            "contract.fluid.yaml",
            "--scheduler",
            "airflow",
            "-o",
            "generated/airflow",
            "--overwrite",
        ],
        cwd=product_dir,
        env=env,
    )

    install_mode = args.install_mode or env.get("JENKINS_INSTALL_MODE") or "dev-source"
    _run(
        [
            str(fluid),
            "generate",
            "ci",
            "contract.fluid.yaml",
            "--system",
            "jenkins",
            "--install-mode",
            install_mode,
            "--default-publish-target",
            "datamesh-manager",
            "--no-verify-strict-default",
            "--publish-stage-default",
            "--no-publish-include-env",
            "--out",
            "Jenkinsfile",
        ],
        cwd=product_dir,
        env=env,
    )

    _write_summary(product_dir, receipt)
    print(f"Wrote MCP B2 contract: {product_dir / 'contract.fluid.yaml'}")
    print(f"Raw MCP forge output: {raw_dir}")
    print(f"Generated B2 dbt project: {dbt_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
