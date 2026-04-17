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
    ("Fiber Home", "fixed_broadband", 500.00, None, 79.00),
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
ADDRESS_ROLES = ["billing", "installation", "service"]
STREET_NAMES = [
    "Bahnhofstrasse",
    "Seefeldweg",
    "Industriestrasse",
    "Marktgasse",
    "Poststrasse",
    "Sonnenweg",
]
CITY_DATA = [
    ("Zurich", "ZH", "8001"),
    ("Bern", "BE", "3001"),
    ("Basel", "BS", "4001"),
    ("Lausanne", "VD", "1003"),
    ("Lucerne", "LU", "6003"),
    ("St. Gallen", "SG", "9000"),
]
CONTACT_MEDIUM_TYPES = ["email", "mobile_phone", "sms", "app_push"]
CONTACT_PURPOSES = ["billing", "support", "marketing", "service"]
PARTY_ROLE_TYPES = ["customer", "billing_contact", "technical_contact", "decision_maker"]
RESOURCE_TYPES = ["sim_profile", "network_slice", "ip_address", "broadband_port"]
INTERACTION_CHANNELS = ["app", "call_center", "store", "chatbot", "email"]
INTERACTION_TYPES = ["plan_review", "billing_question", "support_case", "retention", "upgrade_quote"]
INTERACTION_OUTCOMES = ["resolved", "escalated", "follow_up", "converted", "information_shared"]
TICKET_CATEGORIES = ["connectivity", "billing", "device", "activation", "quality_of_service"]
TICKET_SEVERITIES = ["low", "medium", "high", "critical"]
LIFECYCLE_EVENT_TYPES = ["activation", "upgrade", "suspension", "restoration", "termination"]


TABLE_SPECS: dict[str, TableSpec] = {
    "party": TableSpec(
        "party",
        "TM Forum SID-style master registry for parties participating in the telco domain.",
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
        "Contact and demographic profile for individual parties in the telco domain.",
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
    "geographic_address": TableSpec(
        "geographic_address",
        "Address inventory for party billing, installation, and service locations.",
        [
            ColumnSpec("address_id", "VARCHAR"),
            ColumnSpec("party_id", "VARCHAR"),
            ColumnSpec("address_role", "VARCHAR"),
            ColumnSpec("street_name", "VARCHAR"),
            ColumnSpec("city", "VARCHAR"),
            ColumnSpec("region_code", "VARCHAR"),
            ColumnSpec("postal_code", "VARCHAR"),
            ColumnSpec("country_code", "VARCHAR"),
            ColumnSpec("valid_from", "DATE"),
            ColumnSpec("valid_to", "DATE"),
        ],
    ),
    "contact_medium": TableSpec(
        "contact_medium",
        "Preferred contact channels and contact details for each party.",
        [
            ColumnSpec("contact_medium_id", "VARCHAR"),
            ColumnSpec("party_id", "VARCHAR"),
            ColumnSpec("medium_type", "VARCHAR"),
            ColumnSpec("medium_value", "VARCHAR"),
            ColumnSpec("usage_purpose", "VARCHAR"),
            ColumnSpec("preference_rank", "NUMBER"),
            ColumnSpec("valid_from", "DATE"),
            ColumnSpec("valid_to", "DATE"),
        ],
    ),
    "account": TableSpec(
        "account",
        "Customer account records that group subscriptions, invoices, and service relationships.",
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
    "party_role": TableSpec(
        "party_role",
        "Party-to-account role assignments such as customer, billing contact, or technical contact.",
        [
            ColumnSpec("party_role_id", "VARCHAR"),
            ColumnSpec("party_id", "VARCHAR"),
            ColumnSpec("account_id", "VARCHAR"),
            ColumnSpec("role_type", "VARCHAR"),
            ColumnSpec("status", "VARCHAR"),
            ColumnSpec("assigned_at", "TIMESTAMP_NTZ"),
            ColumnSpec("revoked_at", "TIMESTAMP_NTZ"),
        ],
    ),
    "product_offering": TableSpec(
        "product_offering",
        "Sellable commercial telco offerings available for subscription.",
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
        "Operational service instances provisioned for customer accounts.",
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
        "Commercial subscription records connecting services to product offerings.",
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
    "product_inventory": TableSpec(
        "product_inventory",
        "Customer-owned product instances derived from commercial product offerings.",
        [
            ColumnSpec("product_id", "VARCHAR"),
            ColumnSpec("account_id", "VARCHAR"),
            ColumnSpec("product_offering_id", "VARCHAR"),
            ColumnSpec("service_id", "VARCHAR"),
            ColumnSpec("status", "VARCHAR"),
            ColumnSpec("activated_at", "TIMESTAMP_NTZ"),
            ColumnSpec("terminated_at", "TIMESTAMP_NTZ"),
        ],
    ),
    "resource": TableSpec(
        "resource",
        "Assigned technical resources that support provisioned services.",
        [
            ColumnSpec("resource_id", "VARCHAR"),
            ColumnSpec("service_id", "VARCHAR"),
            ColumnSpec("resource_type", "VARCHAR"),
            ColumnSpec("resource_name", "VARCHAR"),
            ColumnSpec("resource_status", "VARCHAR"),
            ColumnSpec("assigned_at", "TIMESTAMP_NTZ"),
            ColumnSpec("released_at", "TIMESTAMP_NTZ"),
        ],
    ),
    "device": TableSpec(
        "device",
        "Registered customer devices associated with an account.",
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
        "SIM card inventory and assignment records for customer devices.",
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
        "Metered usage events for data, voice, and messaging activity.",
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
        "Digital engagement events captured from the customer-facing application.",
        [
            ColumnSpec("app_event_id", "VARCHAR"),
            ColumnSpec("account_id", "VARCHAR"),
            ColumnSpec("device_id", "VARCHAR"),
            ColumnSpec("event_type", "VARCHAR"),
            ColumnSpec("session_minutes", "NUMBER(8,2)"),
            ColumnSpec("event_timestamp", "TIMESTAMP_NTZ"),
        ],
    ),
    "customer_interaction": TableSpec(
        "customer_interaction",
        "Sales and support interactions across assisted and digital channels.",
        [
            ColumnSpec("interaction_id", "VARCHAR"),
            ColumnSpec("account_id", "VARCHAR"),
            ColumnSpec("service_id", "VARCHAR"),
            ColumnSpec("channel", "VARCHAR"),
            ColumnSpec("interaction_type", "VARCHAR"),
            ColumnSpec("outcome", "VARCHAR"),
            ColumnSpec("interaction_timestamp", "TIMESTAMP_NTZ"),
        ],
    ),
    "trouble_ticket": TableSpec(
        "trouble_ticket",
        "Support tickets raised for billing, connectivity, and service-quality issues.",
        [
            ColumnSpec("ticket_id", "VARCHAR"),
            ColumnSpec("account_id", "VARCHAR"),
            ColumnSpec("service_id", "VARCHAR"),
            ColumnSpec("ticket_category", "VARCHAR"),
            ColumnSpec("severity", "VARCHAR"),
            ColumnSpec("status", "VARCHAR"),
            ColumnSpec("opened_at", "TIMESTAMP_NTZ"),
            ColumnSpec("resolved_at", "TIMESTAMP_NTZ"),
        ],
    ),
    "service_lifecycle_event": TableSpec(
        "service_lifecycle_event",
        "Lifecycle history for operational services, including activation and change events.",
        [
            ColumnSpec("lifecycle_event_id", "VARCHAR"),
            ColumnSpec("service_id", "VARCHAR"),
            ColumnSpec("event_type", "VARCHAR"),
            ColumnSpec("event_reason", "VARCHAR"),
            ColumnSpec("actor_type", "VARCHAR"),
            ColumnSpec("event_timestamp", "TIMESTAMP_NTZ"),
        ],
    ),
    "invoice": TableSpec(
        "invoice",
        "Monthly bill documents issued to customer accounts.",
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
    "invoice_charge": TableSpec(
        "invoice_charge",
        "Detailed charge lines that roll up into customer invoices.",
        [
            ColumnSpec("charge_id", "VARCHAR"),
            ColumnSpec("invoice_id", "VARCHAR"),
            ColumnSpec("charge_type", "VARCHAR"),
            ColumnSpec("charge_description", "VARCHAR"),
            ColumnSpec("quantity", "NUMBER(12,4)"),
            ColumnSpec("amount_chf", "NUMBER(10,2)"),
            ColumnSpec("charge_date", "DATE"),
        ],
    ),
    "payment": TableSpec(
        "payment",
        "Recorded payments that settle issued invoices.",
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
        "Contract and policy acknowledgements associated with customer accounts.",
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
        "Operational and commercial orders used to activate or change services.",
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
    interaction_count = max(800, party_count * 6)

    rows: dict[str, list[dict[str, Any]]] = {table: [] for table in TABLE_SPECS}

    plan_ids: list[str] = []
    account_ids: list[str] = []
    service_ids: list[str] = []
    device_ids: list[str] = []
    invoice_ids: list[str] = []
    account_to_services: dict[str, list[str]] = {}
    service_to_account: dict[str, str] = {}
    service_to_activation: dict[str, datetime] = {}

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
                "created_at": rand_dt(rng, history_days + 45, 5),
            }
        )

    for idx in range(1, party_count + 1):
        party_id = stable_uuid("party", str(idx))
        individual_id = stable_uuid("individual", str(idx))
        account_id = stable_uuid("account", str(idx))
        created_at = rand_dt(rng, history_days + 45, 7)
        first_name = rng.choice(FIRST_NAMES)
        last_name = rng.choice(LAST_NAMES)
        is_business = idx % 17 == 0
        account_status = rng.choices(
            ["active", "active", "active", "active", "suspended", "closed"],
            weights=[40, 30, 20, 10, 6, 2],
        )[0]
        closed_at = rand_dt(rng, 10, 1) if account_status == "closed" else None
        account_type = "business" if is_business else rng.choice(["individual", "prepaid"])

        rows["party"].append(
            {
                "party_id": party_id,
                "party_type": "organization" if is_business else "individual",
                "status": "inactive" if account_status == "closed" else "active",
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
                "account_type": account_type,
                "status": account_status,
                "created_at": created_at,
                "closed_at": closed_at,
            }
        )
        account_ids.append(account_id)

        address_count = 2 if is_business or rng.random() < 0.30 else 1
        for address_num in range(address_count):
            city, region_code, postal_code = rng.choice(CITY_DATA)
            rows["geographic_address"].append(
                {
                    "address_id": stable_uuid("geographic_address", f"{idx}-{address_num}"),
                    "party_id": party_id,
                    "address_role": ADDRESS_ROLES[min(address_num, len(ADDRESS_ROLES) - 1)],
                    "street_name": f"{rng.choice(STREET_NAMES)} {rng.randint(1, 120)}",
                    "city": city,
                    "region_code": region_code,
                    "postal_code": postal_code,
                    "country_code": "CH",
                    "valid_from": (created_at - timedelta(days=30)).date(),
                    "valid_to": None,
                }
            )

        contact_values = [
            ("email", f"{first_name.lower()}.{last_name.lower()}{idx}@example.com"),
            ("mobile_phone", f"+4179{idx:07d}"),
        ]
        if rng.random() < 0.65:
            contact_values.append(("app_push", f"app-user-{idx:06d}"))
        for medium_num, (medium_type, medium_value) in enumerate(contact_values, start=1):
            rows["contact_medium"].append(
                {
                    "contact_medium_id": stable_uuid("contact_medium", f"{idx}-{medium_num}"),
                    "party_id": party_id,
                    "medium_type": medium_type,
                    "medium_value": medium_value,
                    "usage_purpose": CONTACT_PURPOSES[min(medium_num - 1, len(CONTACT_PURPOSES) - 1)],
                    "preference_rank": medium_num,
                    "valid_from": created_at.date(),
                    "valid_to": None,
                }
            )

        party_roles = ["customer"]
        if is_business:
            party_roles.extend(["billing_contact", "technical_contact"])
        elif rng.random() < 0.20:
            party_roles.append("decision_maker")
        for role_num, role_type in enumerate(party_roles, start=1):
            rows["party_role"].append(
                {
                    "party_role_id": stable_uuid("party_role", f"{idx}-{role_num}"),
                    "party_id": party_id,
                    "account_id": account_id,
                    "role_type": role_type,
                    "status": "inactive" if account_status == "closed" else "active",
                    "assigned_at": created_at + timedelta(hours=role_num),
                    "revoked_at": closed_at if account_status == "closed" and role_num > 1 else None,
                }
            )

        account_to_services[account_id] = []
        service_count = rng.choices([1, 2, 3], weights=[55, 30, 15])[0]
        for svc_num in range(service_count):
            service_id = stable_uuid("service", f"{idx}-{svc_num}")
            subscription_id = stable_uuid("subscription", f"{idx}-{svc_num}")
            product_id = stable_uuid("product_inventory", f"{idx}-{svc_num}")
            activated_at = rand_dt(rng, history_days, 3)
            lifecycle_status = rng.choices(
                ["active", "active", "active", "suspended", "terminated"],
                weights=[45, 25, 15, 10, 5],
            )[0]
            terminated_at = rand_dt(rng, 7, 1) if lifecycle_status == "terminated" else None
            service_status = lifecycle_status
            plan_id = rng.choice(plan_ids)

            rows["service"].append(
                {
                    "service_id": service_id,
                    "account_id": account_id,
                    "service_type": rng.choice(SERVICE_TYPES),
                    "status": service_status,
                    "activated_at": activated_at,
                    "terminated_at": terminated_at,
                }
            )
            rows["subscription"].append(
                {
                    "subscription_id": subscription_id,
                    "service_id": service_id,
                    "product_offering_id": plan_id,
                    "status": "cancelled" if lifecycle_status == "terminated" else service_status,
                    "start_date": activated_at.date(),
                    "end_date": terminated_at.date() if terminated_at else None,
                    "renewal_date": (activated_at + timedelta(days=365)).date(),
                    "created_at": activated_at,
                }
            )
            rows["product_inventory"].append(
                {
                    "product_id": product_id,
                    "account_id": account_id,
                    "product_offering_id": plan_id,
                    "service_id": service_id,
                    "status": service_status,
                    "activated_at": activated_at,
                    "terminated_at": terminated_at,
                }
            )

            resource_count = 2 if rng.random() < 0.35 else 1
            for resource_num in range(resource_count):
                resource_type = rng.choice(RESOURCE_TYPES)
                rows["resource"].append(
                    {
                        "resource_id": stable_uuid("resource", f"{idx}-{svc_num}-{resource_num}"),
                        "service_id": service_id,
                        "resource_type": resource_type,
                        "resource_name": f"{resource_type}-{idx:04d}-{svc_num}-{resource_num}",
                        "resource_status": "released" if lifecycle_status == "terminated" else "active",
                        "assigned_at": activated_at + timedelta(minutes=15 * (resource_num + 1)),
                        "released_at": terminated_at,
                    }
                )

            lifecycle_events: list[tuple[str, str, datetime]] = [
                ("activation", "initial_order", activated_at)
            ]
            if rng.random() < 0.35 and lifecycle_status != "terminated":
                lifecycle_events.append(
                    (
                        "upgrade",
                        "commercial_change",
                        activated_at + timedelta(days=rng.randint(10, max(12, history_days // 2))),
                    )
                )
            if lifecycle_status == "suspended":
                lifecycle_events.append(
                    (
                        "suspension",
                        rng.choice(["billing_hold", "fraud_review", "customer_request"]),
                        rand_dt(rng, 15, 1),
                    )
                )
            if lifecycle_status == "terminated" and terminated_at is not None:
                lifecycle_events.append(("termination", "customer_request", terminated_at))
            for event_num, (event_type, event_reason, event_timestamp) in enumerate(lifecycle_events, start=1):
                rows["service_lifecycle_event"].append(
                    {
                        "lifecycle_event_id": stable_uuid(
                            "service_lifecycle_event", f"{idx}-{svc_num}-{event_num}"
                        ),
                        "service_id": service_id,
                        "event_type": event_type,
                        "event_reason": event_reason,
                        "actor_type": rng.choice(["system", "agent", "customer"]),
                        "event_timestamp": event_timestamp,
                    }
                )

            service_ids.append(service_id)
            account_to_services[account_id].append(service_id)
            service_to_account[service_id] = account_id
            service_to_activation[service_id] = activated_at

        device_count = 2 if is_business or rng.random() < 0.20 else 1
        primary_registered_at = rand_dt(rng, history_days, 3)
        for device_num in range(device_count):
            device_id = stable_uuid("device", f"{idx}-{device_num}")
            sim_id = stable_uuid("sim_card", f"{idx}-{device_num}")
            registered_at = primary_registered_at + timedelta(hours=device_num)
            rows["device"].append(
                {
                    "device_id": device_id,
                    "account_id": account_id,
                    "device_type": rng.choice(DEVICE_TYPES),
                    "manufacturer": rng.choice(MANUFACTURERS),
                    "model": rng.choice(MODELS),
                    "imei": f"{100000000000000 + idx * 10 + device_num}",
                    "status": "retired" if account_status == "closed" else "active",
                    "registered_at": registered_at,
                }
            )
            rows["sim_card"].append(
                {
                    "sim_id": sim_id,
                    "account_id": account_id,
                    "device_id": device_id,
                    "msisdn": f"+4170{idx:05d}{device_num:02d}",
                    "iccid": f"894101{idx:010d}{device_num:02d}",
                    "status": "inactive" if account_status == "closed" else "active",
                    "activated_at": registered_at,
                }
            )
            device_ids.append(device_id)

        rows["agreement"].append(
            {
                "agreement_id": stable_uuid("agreement", str(idx)),
                "account_id": account_id,
                "agreement_type": rng.choice(AGREEMENT_TYPES),
                "status": "terminated" if account_status == "closed" else "active",
                "signed_date": (primary_registered_at - timedelta(days=1)).date(),
                "effective_date": primary_registered_at.date(),
                "termination_date": closed_at.date() if closed_at else None,
                "created_at": primary_registered_at,
            }
        )
        rows["service_order"].append(
            {
                "order_id": stable_uuid("service_order", str(idx)),
                "account_id": account_id,
                "order_type": rng.choice(ORDER_TYPES),
                "status": "completed" if account_status != "suspended" else "in_progress",
                "order_date": primary_registered_at - timedelta(hours=12),
                "fulfillment_date": primary_registered_at + timedelta(hours=6),
            }
        )

    for idx in range(usage_event_count):
        usage_type = rng.choice(USAGE_TYPES)
        quantity = {
            "data_mb": round(rng.uniform(1.0, 2000.0), 4),
            "voice_min": round(rng.uniform(1.0, 120.0), 4),
            "sms": float(rng.randint(1, 10)),
        }[usage_type]
        service_id = rng.choice(service_ids)
        rows["usage_event"].append(
            {
                "usage_id": stable_uuid("usage_event", str(idx)),
                "account_id": service_to_account[service_id],
                "service_id": service_id,
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

    for idx in range(interaction_count):
        account_id = rng.choice(account_ids)
        services_for_account = account_to_services.get(account_id, [])
        rows["customer_interaction"].append(
            {
                "interaction_id": stable_uuid("customer_interaction", str(idx)),
                "account_id": account_id,
                "service_id": rng.choice(services_for_account) if services_for_account and rng.random() < 0.75 else None,
                "channel": rng.choice(INTERACTION_CHANNELS),
                "interaction_type": rng.choice(INTERACTION_TYPES),
                "outcome": rng.choice(INTERACTION_OUTCOMES),
                "interaction_timestamp": rand_dt(rng, history_days),
            }
        )

    trouble_ticket_count = max(120, len(service_ids) // 3)
    candidate_services = rng.sample(service_ids, min(trouble_ticket_count, len(service_ids)))
    for idx, service_id in enumerate(candidate_services):
        status = rng.choices(["resolved", "in_progress", "open"], weights=[60, 25, 15])[0]
        opened_at = max(service_to_activation[service_id] + timedelta(days=1), rand_dt(rng, history_days, 1))
        resolved_at = opened_at + timedelta(days=rng.randint(1, 12)) if status == "resolved" else None
        rows["trouble_ticket"].append(
            {
                "ticket_id": stable_uuid("trouble_ticket", str(idx)),
                "account_id": service_to_account[service_id],
                "service_id": service_id,
                "ticket_category": rng.choice(TICKET_CATEGORIES),
                "severity": rng.choice(TICKET_SEVERITIES),
                "status": status,
                "opened_at": opened_at,
                "resolved_at": resolved_at,
            }
        )

    invoice_counter = 0
    for account_id in rng.sample(account_ids, min(150, len(account_ids))):
        invoice_cycles = rng.randint(1, 3)
        for offset in range(invoice_cycles):
            invoice_id = stable_uuid("invoice", f"{account_id}-{offset}")
            invoice_date = (BASE_NOW - timedelta(days=30 * (offset + 1))).date()
            due_date = invoice_date + timedelta(days=30)
            charge_lines: list[tuple[str, str, float, float]] = [
                ("recurring_charge", "Monthly subscription charge", 1.0, round(rng.uniform(19.0, 89.0), 2))
            ]
            if rng.random() < 0.55:
                charge_lines.append(
                    ("usage_charge", "Out-of-bundle usage", round(rng.uniform(1.0, 8.0), 2), round(rng.uniform(2.5, 22.0), 2))
                )
            if rng.random() < 0.25:
                charge_lines.append(
                    ("equipment_fee", "Device installment", 1.0, round(rng.uniform(8.0, 24.0), 2))
                )

            total_amount = round(sum(amount for _charge_type, _description, _quantity, amount in charge_lines), 2)
            paid = rng.random() > 0.12
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

            for charge_num, (charge_type, charge_description, quantity, amount) in enumerate(charge_lines, start=1):
                rows["invoice_charge"].append(
                    {
                        "charge_id": stable_uuid("invoice_charge", f"{invoice_id}-{charge_num}"),
                        "invoice_id": invoice_id,
                        "charge_type": charge_type,
                        "charge_description": charge_description,
                        "quantity": quantity,
                        "amount_chf": f"{amount:.2f}",
                        "charge_date": invoice_date,
                    }
                )

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
            "description": spec.description,
            "file": path.name,
            "row_count": len(rows_by_table[table_name]),
            "sha256": digest,
            "columns": [column.name for column in spec.columns],
        }

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
