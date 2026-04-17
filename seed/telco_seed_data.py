from __future__ import annotations

import csv
import hashlib
import json
import os
import random
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ColumnSpec:
    name: str
    snowflake_type: str


@dataclass(frozen=True)
class TableSpec:
    name: str
    description: str
    columns: list[ColumnSpec]


BASE_NOW = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
UUID_NAMESPACE = uuid.UUID("6f65ba7c-c968-42b1-987a-5f4637b2f181")

FIRST_NAMES = [
    "Alice",
    "Bruno",
    "Carmen",
    "Diego",
    "Elena",
    "Fatima",
    "Giovanni",
    "Hana",
    "Ivan",
    "Julia",
    "Kenji",
    "Layla",
    "Marco",
    "Nadia",
    "Omar",
    "Priya",
    "Quentin",
    "Rosa",
    "Stefan",
    "Tara",
    "Uwe",
    "Vera",
    "Wei",
    "Xena",
    "Yusuf",
    "Zara",
]
LAST_NAMES = [
    "Meier",
    "Mueller",
    "Huber",
    "Keller",
    "Vogel",
    "Roth",
    "Schmidt",
    "Fischer",
    "Bauer",
    "Weber",
    "Zimmermann",
    "Steiner",
    "Brunner",
    "Maier",
    "Wirth",
]
PLAN_DEFS = [
    ("S Basic", "data_plan", 0.50, None, 15.00),
    ("M Standard", "data_plan", 5.00, None, 29.00),
    ("L Premium", "data_plan", 20.00, None, 49.00),
    ("Voice Only", "voice", None, 200, 19.00),
    ("Bundle Pro", "bundle", None, None, 69.00),
]
DEVICE_TYPES = ["smartphone", "tablet", "router", "iot"]
MANUFACTURERS = ["Apple", "Samsung", "Xiaomi", "Huawei", "OnePlus", "Google"]
MODELS = ["Pro Max", "Ultra", "Plus", "Lite", "Standard", "Edge"]
USAGE_TYPES = ["data_mb", "voice_min", "sms"]
APP_EVENT_TYPES = [
    "login",
    "logout",
    "plan_upgrade",
    "plan_browse",
    "support_contact",
    "payment_made",
    "feature_used",
]
PAYMENT_METHODS = ["credit_card", "debit_card", "bank_transfer", "digital_wallet"]
AGREEMENT_TYPES = ["service_contract", "terms_of_service", "data_processing"]
ORDER_TYPES = ["activation", "upgrade", "downgrade", "suspension", "cancellation", "porting"]
SERVICE_TYPES = ["mobile_line", "app_access", "data_only", "fixed_broadband"]


TABLE_SPECS: dict[str, TableSpec] = {
    "party": TableSpec(
        "party",
        "Landing table for party records.",
        [
            ColumnSpec("party_id", "VARCHAR"),
            ColumnSpec("party_type", "VARCHAR"),
            ColumnSpec("status", "VARCHAR"),
            ColumnSpec("created_at", "TIMESTAMP_NTZ"),
            ColumnSpec("updated_at", "TIMESTAMP_NTZ"),
        ],
    ),
    "individual": TableSpec(
        "individual",
        "Landing table for individual customer records.",
        [
            ColumnSpec("individual_id", "VARCHAR"),
            ColumnSpec("party_id", "VARCHAR"),
            ColumnSpec("first_name", "VARCHAR"),
            ColumnSpec("last_name", "VARCHAR"),
            ColumnSpec("email", "VARCHAR"),
            ColumnSpec("date_of_birth", "DATE"),
            ColumnSpec("created_at", "TIMESTAMP_NTZ"),
        ],
    ),
    "account": TableSpec(
        "account",
        "Landing table for account records.",
        [
            ColumnSpec("account_id", "VARCHAR"),
            ColumnSpec("party_id", "VARCHAR"),
            ColumnSpec("account_number", "VARCHAR"),
            ColumnSpec("account_type", "VARCHAR"),
            ColumnSpec("status", "VARCHAR"),
            ColumnSpec("created_at", "TIMESTAMP_NTZ"),
            ColumnSpec("closed_at", "TIMESTAMP_NTZ"),
        ],
    ),
    "product_offering": TableSpec(
        "product_offering",
        "Landing table for product offering records.",
        [
            ColumnSpec("product_offering_id", "VARCHAR"),
            ColumnSpec("name", "VARCHAR"),
            ColumnSpec("category", "VARCHAR"),
            ColumnSpec("data_limit_gb", "NUMBER(8,2)"),
            ColumnSpec("voice_limit_min", "NUMBER"),
            ColumnSpec("price_chf", "NUMBER(10,2)"),
            ColumnSpec("status", "VARCHAR"),
            ColumnSpec("created_at", "TIMESTAMP_NTZ"),
        ],
    ),
    "service": TableSpec(
        "service",
        "Landing table for active service instances.",
        [
            ColumnSpec("service_id", "VARCHAR"),
            ColumnSpec("account_id", "VARCHAR"),
            ColumnSpec("service_type", "VARCHAR"),
            ColumnSpec("status", "VARCHAR"),
            ColumnSpec("activated_at", "TIMESTAMP_NTZ"),
            ColumnSpec("terminated_at", "TIMESTAMP_NTZ"),
        ],
    ),
    "subscription": TableSpec(
        "subscription",
        "Landing table for service subscriptions.",
        [
            ColumnSpec("subscription_id", "VARCHAR"),
            ColumnSpec("service_id", "VARCHAR"),
            ColumnSpec("product_offering_id", "VARCHAR"),
            ColumnSpec("status", "VARCHAR"),
            ColumnSpec("start_date", "DATE"),
            ColumnSpec("end_date", "DATE"),
            ColumnSpec("renewal_date", "DATE"),
            ColumnSpec("created_at", "TIMESTAMP_NTZ"),
        ],
    ),
    "device": TableSpec(
        "device",
        "Landing table for registered devices.",
        [
            ColumnSpec("device_id", "VARCHAR"),
            ColumnSpec("account_id", "VARCHAR"),
            ColumnSpec("device_type", "VARCHAR"),
            ColumnSpec("manufacturer", "VARCHAR"),
            ColumnSpec("model", "VARCHAR"),
            ColumnSpec("imei", "VARCHAR"),
            ColumnSpec("status", "VARCHAR"),
            ColumnSpec("registered_at", "TIMESTAMP_NTZ"),
        ],
    ),
    "sim_card": TableSpec(
        "sim_card",
        "Landing table for SIM card assignments.",
        [
            ColumnSpec("sim_id", "VARCHAR"),
            ColumnSpec("account_id", "VARCHAR"),
            ColumnSpec("device_id", "VARCHAR"),
            ColumnSpec("msisdn", "VARCHAR"),
            ColumnSpec("iccid", "VARCHAR"),
            ColumnSpec("status", "VARCHAR"),
            ColumnSpec("activated_at", "TIMESTAMP_NTZ"),
        ],
    ),
    "usage_event": TableSpec(
        "usage_event",
        "Landing table for raw usage events.",
        [
            ColumnSpec("usage_id", "VARCHAR"),
            ColumnSpec("account_id", "VARCHAR"),
            ColumnSpec("service_id", "VARCHAR"),
            ColumnSpec("usage_type", "VARCHAR"),
            ColumnSpec("quantity", "NUMBER(12,4)"),
            ColumnSpec("event_timestamp", "TIMESTAMP_NTZ"),
            ColumnSpec("rating_status", "VARCHAR"),
        ],
    ),
    "app_event": TableSpec(
        "app_event",
        "Landing table for app engagement events.",
        [
            ColumnSpec("app_event_id", "VARCHAR"),
            ColumnSpec("account_id", "VARCHAR"),
            ColumnSpec("device_id", "VARCHAR"),
            ColumnSpec("event_type", "VARCHAR"),
            ColumnSpec("session_minutes", "NUMBER(8,2)"),
            ColumnSpec("event_timestamp", "TIMESTAMP_NTZ"),
        ],
    ),
    "invoice": TableSpec(
        "invoice",
        "Landing table for monthly invoices.",
        [
            ColumnSpec("invoice_id", "VARCHAR"),
            ColumnSpec("account_id", "VARCHAR"),
            ColumnSpec("invoice_number", "VARCHAR"),
            ColumnSpec("invoice_date", "DATE"),
            ColumnSpec("due_date", "DATE"),
            ColumnSpec("total_amount_chf", "NUMBER(10,2)"),
            ColumnSpec("status", "VARCHAR"),
            ColumnSpec("created_at", "TIMESTAMP_NTZ"),
        ],
    ),
    "payment": TableSpec(
        "payment",
        "Landing table for invoice payments.",
        [
            ColumnSpec("payment_id", "VARCHAR"),
            ColumnSpec("invoice_id", "VARCHAR"),
            ColumnSpec("amount_chf", "NUMBER(10,2)"),
            ColumnSpec("payment_method", "VARCHAR"),
            ColumnSpec("payment_date", "DATE"),
            ColumnSpec("status", "VARCHAR"),
            ColumnSpec("created_at", "TIMESTAMP_NTZ"),
        ],
    ),
    "agreement": TableSpec(
        "agreement",
        "Landing table for agreement records.",
        [
            ColumnSpec("agreement_id", "VARCHAR"),
            ColumnSpec("account_id", "VARCHAR"),
            ColumnSpec("agreement_type", "VARCHAR"),
            ColumnSpec("status", "VARCHAR"),
            ColumnSpec("signed_date", "DATE"),
            ColumnSpec("effective_date", "DATE"),
            ColumnSpec("termination_date", "DATE"),
            ColumnSpec("created_at", "TIMESTAMP_NTZ"),
        ],
    ),
    "service_order": TableSpec(
        "service_order",
        "Landing table for service orders.",
        [
            ColumnSpec("order_id", "VARCHAR"),
            ColumnSpec("account_id", "VARCHAR"),
            ColumnSpec("order_type", "VARCHAR"),
            ColumnSpec("status", "VARCHAR"),
            ColumnSpec("order_date", "TIMESTAMP_NTZ"),
            ColumnSpec("fulfillment_date", "TIMESTAMP_NTZ"),
        ],
    ),
}


def stable_uuid(namespace: str, value: str) -> str:
    return str(uuid.uuid5(UUID_NAMESPACE, f"{namespace}:{value}"))


def env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def rand_dt(rng: random.Random, max_days_back: int, min_days_back: int = 0) -> datetime:
    seconds = rng.randint(min_days_back * 86400, max_days_back * 86400)
    return BASE_NOW - timedelta(seconds=seconds)


def render_value(value: Any) -> str:
    if value is None:
        return "\\N"
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)


def build_dataset() -> dict[str, list[dict[str, Any]]]:
    rng = random.Random(env_int("TELCO_SEED_RANDOM_SEED", 42))
    party_count = env_int("TELCO_SEED_PARTY_COUNT", 200)
    usage_event_count = env_int("TELCO_SEED_USAGE_EVENT_COUNT", 10000)
    app_event_count = env_int("TELCO_SEED_APP_EVENT_COUNT", 2000)
    history_days = env_int("TELCO_SEED_HISTORY_DAYS", 60)

    rows: dict[str, list[dict[str, Any]]] = {table: [] for table in TABLE_SPECS}

    plan_ids: list[str] = []
    for idx, (name, category, data_limit, voice_limit, price_chf) in enumerate(PLAN_DEFS, start=1):
        plan_id = stable_uuid("product_offering", str(idx))
        plan_ids.append(plan_id)
        rows["product_offering"].append(
            {
                "product_offering_id": plan_id,
                "name": name,
                "category": category,
                "data_limit_gb": data_limit,
                "voice_limit_min": voice_limit,
                "price_chf": f"{price_chf:.2f}",
                "status": "active",
                "created_at": rand_dt(rng, history_days + 30, 1),
            }
        )

    account_ids: list[str] = []
    service_ids: list[str] = []
    device_ids: list[str] = []
    invoice_ids: list[str] = []

    for idx in range(1, party_count + 1):
        party_id = stable_uuid("party", str(idx))
        individual_id = stable_uuid("individual", str(idx))
        account_id = stable_uuid("account", str(idx))
        created_at = rand_dt(rng, history_days + 30, 5)
        first_name = rng.choice(FIRST_NAMES)
        last_name = rng.choice(LAST_NAMES)

        rows["party"].append(
            {
                "party_id": party_id,
                "party_type": "organization" if idx % 17 == 0 else "individual",
                "status": "active",
                "created_at": created_at,
                "updated_at": created_at + timedelta(days=1),
            }
        )
        rows["individual"].append(
            {
                "individual_id": individual_id,
                "party_id": party_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": f"{first_name.lower()}.{last_name.lower()}{idx}@example.com",
                "date_of_birth": (BASE_NOW - timedelta(days=365 * rng.randint(19, 70))).date(),
                "created_at": created_at,
            }
        )
        rows["account"].append(
            {
                "account_id": account_id,
                "party_id": party_id,
                "account_number": f"ACC{idx:06d}",
                "account_type": rng.choice(["individual", "business", "prepaid"]),
                "status": "active",
                "created_at": created_at,
                "closed_at": None,
            }
        )
        account_ids.append(account_id)

        service_count = rng.choices([1, 2, 3], weights=[60, 30, 10])[0]
        for svc_num in range(service_count):
            service_id = stable_uuid("service", f"{idx}-{svc_num}")
            subscription_id = stable_uuid("subscription", f"{idx}-{svc_num}")
            activated_at = rand_dt(rng, history_days, 2)
            maybe_terminated = rand_dt(rng, 5) if rng.random() < 0.05 else None
            rows["service"].append(
                {
                    "service_id": service_id,
                    "account_id": account_id,
                    "service_type": rng.choice(SERVICE_TYPES),
                    "status": "terminated" if maybe_terminated else "active",
                    "activated_at": activated_at,
                    "terminated_at": maybe_terminated,
                }
            )
            rows["subscription"].append(
                {
                    "subscription_id": subscription_id,
                    "service_id": service_id,
                    "product_offering_id": rng.choice(plan_ids),
                    "status": "cancelled" if maybe_terminated else "active",
                    "start_date": activated_at.date(),
                    "end_date": maybe_terminated.date() if maybe_terminated else None,
                    "renewal_date": (activated_at + timedelta(days=365)).date(),
                    "created_at": activated_at,
                }
            )
            service_ids.append(service_id)

        device_id = stable_uuid("device", str(idx))
        sim_id = stable_uuid("sim_card", str(idx))
        registered_at = rand_dt(rng, history_days, 3)
        rows["device"].append(
            {
                "device_id": device_id,
                "account_id": account_id,
                "device_type": rng.choice(DEVICE_TYPES),
                "manufacturer": rng.choice(MANUFACTURERS),
                "model": rng.choice(MODELS),
                "imei": f"{100000000000000 + idx}",
                "status": "active",
                "registered_at": registered_at,
            }
        )
        rows["sim_card"].append(
            {
                "sim_id": sim_id,
                "account_id": account_id,
                "device_id": device_id,
                "msisdn": f"+4170{idx:07d}",
                "iccid": f"894101{idx:012d}",
                "status": "active",
                "activated_at": registered_at,
            }
        )
        rows["agreement"].append(
            {
                "agreement_id": stable_uuid("agreement", str(idx)),
                "account_id": account_id,
                "agreement_type": rng.choice(AGREEMENT_TYPES),
                "status": "active",
                "signed_date": (registered_at - timedelta(days=1)).date(),
                "effective_date": registered_at.date(),
                "termination_date": None,
                "created_at": registered_at,
            }
        )
        rows["service_order"].append(
            {
                "order_id": stable_uuid("service_order", str(idx)),
                "account_id": account_id,
                "order_type": rng.choice(ORDER_TYPES),
                "status": rng.choice(["pending", "in_progress", "completed"]),
                "order_date": registered_at - timedelta(hours=12),
                "fulfillment_date": registered_at + timedelta(hours=6),
            }
        )
        device_ids.append(device_id)

    for idx in range(usage_event_count):
        usage_type = rng.choice(USAGE_TYPES)
        quantity = {
            "data_mb": round(rng.uniform(1.0, 2000.0), 4),
            "voice_min": round(rng.uniform(1.0, 120.0), 4),
            "sms": float(rng.randint(1, 10)),
        }[usage_type]
        rows["usage_event"].append(
            {
                "usage_id": stable_uuid("usage_event", str(idx)),
                "account_id": rng.choice(account_ids),
                "service_id": rng.choice(service_ids),
                "usage_type": usage_type,
                "quantity": quantity,
                "event_timestamp": rand_dt(rng, history_days),
                "rating_status": rng.choice(["rated", "rated", "rated", "unrated", "error"]),
            }
        )

    for idx in range(app_event_count):
        rows["app_event"].append(
            {
                "app_event_id": stable_uuid("app_event", str(idx)),
                "account_id": rng.choice(account_ids),
                "device_id": rng.choice(device_ids),
                "event_type": rng.choice(APP_EVENT_TYPES),
                "session_minutes": round(rng.uniform(0.5, 45.0), 2),
                "event_timestamp": rand_dt(rng, history_days),
            }
        )

    invoice_counter = 0
    for account_id in rng.sample(account_ids, min(150, len(account_ids))):
        invoice_cycles = rng.randint(1, 3)
        for offset in range(invoice_cycles):
            invoice_id = stable_uuid("invoice", f"{account_id}-{offset}")
            invoice_date = (BASE_NOW - timedelta(days=30 * (offset + 1))).date()
            due_date = invoice_date + timedelta(days=30)
            total_amount = round(rng.uniform(15.0, 150.0), 2)
            paid = rng.random() > 0.1
            status = "paid" if paid else "overdue"

            rows["invoice"].append(
                {
                    "invoice_id": invoice_id,
                    "account_id": account_id,
                    "invoice_number": f"INV{invoice_counter:07d}",
                    "invoice_date": invoice_date,
                    "due_date": due_date,
                    "total_amount_chf": f"{total_amount:.2f}",
                    "status": status,
                    "created_at": datetime.combine(invoice_date, datetime.min.time(), tzinfo=timezone.utc),
                }
            )
            invoice_ids.append(invoice_id)
            invoice_counter += 1

            if paid:
                rows["payment"].append(
                    {
                        "payment_id": stable_uuid("payment", f"{invoice_id}-1"),
                        "invoice_id": invoice_id,
                        "amount_chf": f"{total_amount:.2f}",
                        "payment_method": rng.choice(PAYMENT_METHODS),
                        "payment_date": due_date - timedelta(days=rng.randint(0, 10)),
                        "status": "completed",
                        "created_at": datetime.combine(invoice_date, datetime.min.time(), tzinfo=timezone.utc)
                        + timedelta(days=1),
                    }
                )

    return rows


def write_dataset(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows_by_table = build_dataset()
    manifest: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tables": {},
    }

    for table_name, spec in TABLE_SPECS.items():
        path = output_dir / f"{table_name}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=[column.name for column in spec.columns])
            writer.writeheader()
            for row in rows_by_table[table_name]:
                writer.writerow({key: render_value(value) for key, value in row.items()})
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest["tables"][table_name] = {
            "file": path.name,
            "row_count": len(rows_by_table[table_name]),
            "sha256": digest,
            "columns": [column.name for column in spec.columns],
        }

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
