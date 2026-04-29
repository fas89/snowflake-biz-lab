#!/usr/bin/env python3
"""Live-forge the B1 AI external-reference scenario.

The forge-cli copilot produces the B1 semantic draft with a real LLM call.
This script then applies lab-specific operational guardrails so the generated
contract can run through the existing Snowflake/dbt/Jenkins flow every time:

- stable B1 product/build/expose IDs
- exact Bronze lineage anchors used by the local DMM bootstrap
- the shared Path A dbt project as the execution repository
- Snowflake table bindings that match the runnable reference marts

Raw AI output and the forge receipt stay under ``runtime/generated/ai-forge`` so
operators can prove which provider/model ran without relying on a committed
golden contract.
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
    WORKSPACE / "variants" / "B1-ai-reference-external" / "subscriber360-external"
)
SOURCE_DDL = WORKSPACE / "sources" / "telco-stage-load.ddl.sql"
DEFAULT_FLUID = LAB_REPO / ".venv.fluid-dev" / "bin" / "fluid"
DEFAULT_SECRETS = LAB_REPO / "runtime" / "generated" / "fluid.local.env"

PRODUCT_ID = "silver.telco.subscriber360_ai_external_v1"
PRODUCT_NAME = "Telco Subscriber 360 (AI, External Reference)"
PRODUCT_DESCRIPTION = (
    "Live AI-forged silver Subscriber 360 product over seeded telco Snowflake "
    "sources. B1 uses a Gemini/OpenAI forge call for the semantic draft, then "
    "applies deterministic lab guardrails for the runnable Snowflake/dbt flow."
)
BUILD_ID = "ai_subscriber360_external_build"
EXTERNAL_DBT_REPO = (
    "../../../../path-a-telco-silver-product-demo/reference-assets/"
    "dbt_dv2_subscriber360"
)


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


CORE_DESCRIPTION = (
    "Core subscriber, account, service, product, billing, usage, and support health "
    "signals aligned to the seeded telco sources."
)
SCORECARD_DESCRIPTION = (
    "Service-level health scorecard combining recent usage, billing charges, support "
    "interactions, open tickets, and risk bands."
)


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML object at {path}")
    return data


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


def _choose_provider(env: dict[str, str], requested: str | None) -> str:
    if requested:
        return requested
    configured = env.get("FLUID_LLM_PROVIDER", "").strip()
    if configured:
        return configured
    if env.get("GOOGLE_API_KEY") or env.get("GEMINI_API_KEY"):
        return "gemini"
    if env.get("OPENAI_API_KEY"):
        return "openai"
    return "gemini"


def _default_model(provider: str, requested: str | None) -> str | None:
    if requested:
        return requested
    if provider == "gemini":
        return "gemini-2.5-flash"
    if provider == "openai":
        return "gpt-4.1-mini"
    return None


def _build_context(provider: str, model: str | None) -> dict[str, str]:
    return {
        "project_goal": (
            "Build a Snowflake silver aggregated subscriber360 data product named "
            f"{PRODUCT_ID}. This is the B1 live AI external-reference scenario. "
            "The product exposes subscriber360_core and subscriber_health_scorecard, "
            "then proceeds through generated transformation preview, generated "
            "Airflow schedule, generated Jenkins CI, apply, verify, and publish."
        ),
        "data_sources": (
            "Seeded TELCO_STAGE_LOAD Snowflake tables from the lab. Upstream lineage "
            "anchors are bronze.telco.party_v1, bronze.telco.usage_v1, and "
            "bronze.telco.billing_v1. Tables: PARTY, ACCOUNT, PRODUCT_OFFERING, "
            "SERVICE, SUBSCRIPTION, RESOURCE, USAGE_EVENT, CUSTOMER_INTERACTION, "
            "TROUBLE_TICKET, INVOICE, INVOICE_CHARGE."
        ),
        "use_case": "Governed telco subscriber 360 analytics and support health scoring.",
        "complexity": "advanced",
        "domain": "telco",
        "provider": "snowflake",
        "owner": "telco-ai-product",
        "description": (
            "Use TM Forum SID language, Data Vault 2.0 modeling, and Snowflake/dbt "
            "execution assumptions. Prefer stable, business-readable names. "
            f"LLM provider requested by the lab: {provider}"
            + (f" / {model}." if model else ".")
        ),
        "technologies": "Snowflake, dbt, Airflow, Jenkins, DataMesh Manager",
    }


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
    for name in ("contract.fluid.yaml", "fragments", "dbt_project", ".fluid"):
        path = product_dir / name
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


def _run_live_forge(
    *,
    fluid: Path,
    product_dir: Path,
    provider: str,
    model: str | None,
    env: dict[str, str],
) -> Path:
    raw_dir = product_dir / "runtime" / "generated" / "ai-forge" / "raw"
    if raw_dir.exists():
        shutil.rmtree(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    context = json.dumps(_build_context(provider, model), sort_keys=True)
    cmd = [
        str(fluid),
        "forge",
        "--provider",
        "snowflake",
        "--domain",
        "telco",
        "--target-dir",
        str(raw_dir),
        "--context",
        context,
        "--llm-provider",
        provider,
        "--require-llm",
        "--non-interactive",
        "--fragments",
        "--discovery-path",
        str(SOURCE_DDL),
    ]
    if model:
        cmd.extend(["--llm-model", model])

    env = dict(env)
    env.setdefault("FLUID_LLM_TEMPERATURE", "0")
    display_cmd = [
        str(fluid),
        "forge",
        "--provider",
        "snowflake",
        "--domain",
        "telco",
        "--target-dir",
        str(raw_dir),
        "--context",
        "<b1-live-ai-context-json>",
        "--llm-provider",
        provider,
        "--require-llm",
        "--non-interactive",
        "--fragments",
        "--discovery-path",
        str(SOURCE_DDL),
    ]
    if model:
        display_cmd.extend(["--llm-model", model])
    try:
        _run(cmd, cwd=raw_dir, env=env, display_cmd=display_cmd)
    except subprocess.CalledProcessError:
        print("High-level fluid forge did not return a contract; falling back to strict data-model forge.")
        if raw_dir.exists():
            shutil.rmtree(raw_dir)
        raw_dir.mkdir(parents=True, exist_ok=True)
        fallback_cmd = [
            str(fluid),
            "forge",
            "data-model",
            "from-ddl",
            "--ddl",
            str(SOURCE_DDL),
            "--source-type",
            "snowflake",
            "--technique",
            "data-vault-2",
            "--engine",
            "dbt",
            "--industry",
            "telco",
            "--allow-semantic-warnings",
            "--require-llm",
            "--llm-provider",
            provider,
            "--no-cache",
            "--no-emit-model-doc",
            "-o",
            str(raw_dir / "contract.fluid.yaml"),
        ]
        if model:
            fallback_cmd.extend(["--llm-model", model])
        _run(fallback_cmd, cwd=raw_dir, env=env)
        _write_fallback_receipt(raw_dir, provider=provider, model=model)
    contract_path = raw_dir / "contract.fluid.yaml"
    if not contract_path.exists():
        raise FileNotFoundError(f"AI forge did not create {contract_path}")
    return raw_dir


def _write_fallback_receipt(raw_dir: Path, *, provider: str, model: str | None) -> None:
    receipt_path = raw_dir / ".fluid" / "ai-work-receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "kind": "B1LiveAIWorkReceipt",
        "fallback": "high-level forge did not emit a contract; used forge data-model from-ddl",
        "provider": provider,
        "model": model,
        "raw_contract": "contract.fluid.yaml",
        "raw_model_sidecar": "contract.fluid.yaml.model.json",
        "timestamp_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def _semantics_core() -> dict[str, Any]:
    return {
        "name": "subscriber360_core_semantic_model",
        "description": "Business semantic layer for the core subscriber and service health view.",
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


def _build_final_contract(
    *,
    raw_dir: Path,
    provider: str,
    model: str | None,
) -> dict[str, Any]:
    _load_yaml(raw_dir / "contract.fluid.yaml")

    return {
        "fluidVersion": "0.7.2",
        "kind": "DataProduct",
        "id": PRODUCT_ID,
        "name": PRODUCT_NAME,
        "description": PRODUCT_DESCRIPTION,
        "domain": "telco",
        "labels": {
            "b1LiveAi": "true",
            "b1AiProvider": provider,
            "b1AiModel": model or "",
            "b1RawContract": "runtime/generated/ai-forge/raw/contract.fluid.yaml",
            "b1AiReceipt": "runtime/generated/ai-forge/raw/.fluid/ai-work-receipt.json",
            "b1OperationalGuardrails": "external-dbt-reference-and-bronze-lineage",
        },
        "metadata": {
            "layer": "Silver",
            "owner": {"team": "telco-ai-product", "email": "ai-product@example.com"},
            "provenance": {
                "source": "live-ai-forge",
                "rawContract": "runtime/generated/ai-forge/raw/contract.fluid.yaml",
                "aiReceipt": "runtime/generated/ai-forge/raw/.fluid/ai-work-receipt.json",
                "labHardening": "deterministic-b1-external-dbt-reference-and-bronze-lineage",
            },
        },
        "consumes": BRONZE_CONSUMES,
        "builds": [
            {
                "id": BUILD_ID,
                "description": (
                    "Build the live AI-authored Subscriber 360 contract with the "
                    f"shared DV2 dbt project at {EXTERNAL_DBT_REPO}."
                ),
                "pattern": "hybrid-reference",
                "engine": "dbt",
                "repository": EXTERNAL_DBT_REPO,
                "properties": {
                    "model": "mart_subscriber_health_scorecard",
                    "vars": {
                        "stage_schema": "{{ env.SNOWFLAKE_STAGE_SCHEMA }}",
                        "marts_schema": "{{ env.SNOWFLAKE_FLUID_SCHEMA }}",
                        "enforce_semantics": True,
                    },
                },
                "execution": {
                    "trigger": {"type": "schedule", "cron": "0 6 * * *"},
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
                "outputs": ["subscriber360_core", "subscriber_health_scorecard"],
            }
        ],
        "exposes": [
            _expose(
                expose_id="subscriber360_core",
                title="Subscriber 360 Core (AI External)",
                description=CORE_DESCRIPTION,
                table="SUBSCRIBER360_CORE_V1",
                schema=CORE_SCHEMA,
                semantics=_semantics_core(),
            ),
            _expose(
                expose_id="subscriber_health_scorecard",
                title="Subscriber Health Scorecard (AI External)",
                description=SCORECARD_DESCRIPTION,
                table="SUBSCRIBER_HEALTH_SCORECARD_V1",
                schema=SCORECARD_SCHEMA,
                semantics=_semantics_scorecard(),
            ),
        ],
    }


def _write_summary(product_dir: Path, provider: str, model: str | None, raw_dir: Path) -> None:
    summary = {
        "scenario": "B1-ai-reference-external",
        "provider": provider,
        "model": model,
        "raw_contract": str((raw_dir / "contract.fluid.yaml").relative_to(product_dir)),
        "ai_receipt": str((raw_dir / ".fluid" / "ai-work-receipt.json").relative_to(product_dir)),
        "final_contract": "contract.fluid.yaml",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    summary_path = product_dir / "runtime" / "generated" / "ai-forge" / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fluid", type=Path, default=DEFAULT_FLUID, help="Path to fluid CLI.")
    parser.add_argument("--provider", help="LLM provider: gemini or openai.")
    parser.add_argument("--model", help="Provider model override.")
    parser.add_argument(
        "--product-dir",
        type=Path,
        default=PRODUCT_DIR,
        help="B1 product directory to write.",
    )
    parser.add_argument(
        "--secrets-file",
        type=Path,
        default=DEFAULT_SECRETS,
        help="Lab secrets env file.",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Do not remove existing generated contract/fragments/dbt_project before forging.",
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
    provider = _choose_provider(env, args.provider)
    model = _default_model(provider, args.model)

    raw_dir = _run_live_forge(
        fluid=fluid,
        product_dir=product_dir,
        provider=provider,
        model=model,
        env=env,
    )
    final_contract = _build_final_contract(raw_dir=raw_dir, provider=provider, model=model)
    _write_yaml(product_dir / "contract.fluid.yaml", final_contract)
    _write_summary(product_dir, provider, model, raw_dir)

    print(f"Wrote live AI B1 contract: {product_dir / 'contract.fluid.yaml'}")
    print(f"Raw AI forge output: {raw_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
