"""C1 — Compose Customer 360 CDP from B1 + B2 silver products.

C1 demonstrates the cross-product authoring story that B1 + B2 alone
can't show:

* **``--from-product`` composition** — forge-cli's composition
  pipeline (``fluid_build/forge_datamodel/from_data_products/
  pipeline.py``) resolves both upstream contracts, validates the
  SDP/ADP/CDP rules (CDP accepts SDP+ADP, rejects CDP→CDP), and
  pre-fills ``consumes[]`` with each upstream's exposes.
* **PII propagation** — when an upstream column is tagged
  ``sensitivity: pii``, the ``propagate_pii_classifications`` helper
  copies the tag onto the downstream column with a matching name.
  No manual relabelling required.
* **Cross-product join-key inference** — LogicalAgent reads the
  upstream schemas + the user intent ("aggregate per account per
  month") and proposes the join keys. BuilderAgent emits the dbt
  SQL.
* **SDP/ADP/CDP equivalence axiom** — C1 is gold/CDP, both upstreams
  are silver/ADP. Forge validates the rule before composing.

Lab hardening:

* Stamp ``provenance.scenario: C1-compose-cdp`` + the upstream
  product IDs B1 and B2 are composed from.
* Pin ``builds[*].repository: ./dbt_customer_360`` so apply
  provisions schema only; the in-workspace dbt project owns the
  table.

Usage:

  task c1:forge
  FLUID_LIVE_AI=0 task c1:forge       # golden replay
"""

# ruff: noqa: T201  # CLI scripts intentionally print to stdout for the operator.

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from _ai_forge_common import (  # noqa: E402
    REPO_ROOT,
    run_forge_with_fallback,
    stamp_provenance_label,
)

SCENARIO = "C1-compose-cdp"
TARGET_REL = (
    "gitlab/path-b-ai-telco-silver-import-demo/variants/"
    "C1-compose-cdp/customer_360_cdp"
)

# Upstream contracts forge-cli's composition pipeline reads to
# pre-fill consumes[] and propagate PII tags.
B1_CONTRACT_REL = (
    "gitlab/path-b-ai-telco-silver-import-demo/variants/"
    "B1-ai-reference-external/subscriber360-external/contract.fluid.yaml"
)
B2_CONTRACT_REL = (
    "gitlab/path-b-ai-telco-silver-import-demo/variants/"
    "B2-ai-generate-in-workspace/subscriber360-generated/contract.fluid.yaml"
)


def harden_c1_contract(contract_path: Path, *, b1_path: Path, b2_path: Path) -> None:
    """Apply C1-specific lab guardrails. Idempotent.

    Confirms the ``consumes[]`` block lists both B1 and B2 product IDs.
    If the live forge skipped that for some reason, we patch it in
    from the upstream contracts so the composition is observable
    even when the LogicalAgent didn't fully infer the binding.
    """
    doc = yaml.safe_load(contract_path.read_text(encoding="utf-8")) or {}

    # Equivalence axiom: gold/CDP.
    metadata = doc.setdefault("metadata", {})
    metadata.setdefault("layer", "Gold")
    metadata.setdefault("productType", "CDP")

    # In-workspace dbt for the aggregation.
    builds = doc.get("builds")
    if isinstance(builds, list):
        for b in builds:
            if not isinstance(b, dict):
                continue
            b.setdefault("pattern", "hybrid-reference")
            b.setdefault("engine", "dbt")
            b.setdefault("repository", "./dbt_customer_360")

    # Ensure consumes[] mentions both upstreams. Read each upstream's
    # ``id`` so we don't hardcode names that drift.
    expected_upstream_ids = []
    for up in (b1_path, b2_path):
        if up.exists():
            up_doc = yaml.safe_load(up.read_text(encoding="utf-8")) or {}
            up_id = up_doc.get("id")
            if up_id:
                expected_upstream_ids.append(up_id)

    consumes = doc.get("consumes") or []
    consumes_ids = {c.get("productId") for c in consumes if isinstance(c, dict)}
    missing = [u for u in expected_upstream_ids if u not in consumes_ids]
    if missing:
        # Best-effort: append a stub consumes[] entry for each missing
        # upstream. Operators can refine after the demo.
        for up_id in missing:
            consumes.append(
                {
                    "productId": up_id,
                    "exposeId": "subscriber360_core",
                    "purpose": f"composition input from {up_id} (lab-stub)",
                }
            )
        doc["consumes"] = consumes

    if doc.get("fluidVersion", "0.7.2") < "0.7.3":
        doc["fluidVersion"] = "0.7.3"

    contract_path.write_text(
        yaml.safe_dump(doc, sort_keys=False), encoding="utf-8"
    )


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Drive the C1 composition forge cycle.")
    p.add_argument("--target-dir", default=str(REPO_ROOT / TARGET_REL))
    p.add_argument(
        "--fluid-bin",
        default=str(REPO_ROOT / ".venv.fluid-dev/bin/fluid"),
    )
    p.add_argument(
        "--b1-contract",
        default=str(REPO_ROOT / B1_CONTRACT_REL),
        help="Upstream B1 contract path passed to --from-product",
    )
    p.add_argument(
        "--b2-contract",
        default=str(REPO_ROOT / B2_CONTRACT_REL),
        help="Upstream B2 contract path passed to --from-product",
    )
    args = p.parse_args(argv)

    target_dir = Path(args.target_dir).resolve()
    fluid_bin = Path(args.fluid_bin).resolve()
    b1_contract = Path(args.b1_contract).resolve()
    b2_contract = Path(args.b2_contract).resolve()

    if not fluid_bin.exists():
        print(f"[c1:forge] FATAL: fluid CLI not found at {fluid_bin}", file=sys.stderr)
        return 2
    for up in (b1_contract, b2_contract):
        if not up.exists():
            print(
                f"[c1:forge] FATAL: upstream contract missing at {up}. "
                "Run `task b1:forge` and `task b2:forge` first.",
                file=sys.stderr,
            )
            return 2

    print(f"[c1:forge] scenario={SCENARIO}")
    print(f"[c1:forge] target_dir={target_dir}")
    print(f"[c1:forge] composing from B1: {b1_contract.relative_to(REPO_ROOT)}")
    print(f"[c1:forge] composing from B2: {b2_contract.relative_to(REPO_ROOT)}")

    forge_env = os.environ.copy()
    forge_env.pop("FLUID_FORGE_LEGACY_COPILOT", None)

    result = run_forge_with_fallback(
        scenario=SCENARIO,
        target_dir=target_dir,
        fluid_bin=fluid_bin,
        data_product_type="CDP",
        domain="telco",
        # Composition: feed both upstream paths via --from-product so
        # the composition pipeline resolves them and pre-fills consumes[].
        extra_argv=[
            "--from-product",
            str(b1_contract),
            "--from-product",
            str(b2_contract),
        ],
        env=forge_env,
    )

    print(
        f"[c1:forge] mode={result.mode} provider={result.provider.provider} "
        f"model={result.provider.model} rc={result.rc}"
    )
    if result.receipt_dir:
        try:
            rel = result.receipt_dir.relative_to(REPO_ROOT)
        except ValueError:
            rel = result.receipt_dir
        print(f"[c1:forge] receipt: {rel}")

    if not result.contract_path.exists():
        print("[c1:forge] FATAL: contract not found", file=sys.stderr)
        return 1

    harden_c1_contract(
        result.contract_path,
        b1_path=b1_contract,
        b2_path=b2_contract,
    )
    stamp_provenance_label(
        result.contract_path,
        scenario=SCENARIO,
        mode=result.mode,
        provider=result.provider,
        receipt_dir=result.receipt_dir,
    )

    # Add an explicit C1-only label tracking which upstreams composed in.
    doc = yaml.safe_load(result.contract_path.read_text(encoding="utf-8"))
    labels = doc.setdefault("labels", {})
    labels["provenance.composedFrom"] = "B1+B2"
    labels["provenance.b1ContractPath"] = str(b1_contract.relative_to(REPO_ROOT))
    labels["provenance.b2ContractPath"] = str(b2_contract.relative_to(REPO_ROOT))
    result.contract_path.write_text(
        yaml.safe_dump(doc, sort_keys=False), encoding="utf-8"
    )

    # Validate.
    import subprocess

    val = subprocess.run(
        [str(fluid_bin), "validate", str(result.contract_path)],
        capture_output=True,
        text=True,
    )
    print(val.stdout.splitlines()[-1] if val.stdout else "(no validate output)")
    if val.returncode != 0:
        print(val.stderr, file=sys.stderr)
        return 1

    # Sanity: assert consumes[] has both upstreams.
    final_doc = yaml.safe_load(result.contract_path.read_text(encoding="utf-8"))
    upstream_ids = {
        c.get("productId")
        for c in (final_doc.get("consumes") or [])
        if isinstance(c, dict)
    }
    print(f"[c1:forge] composes from: {sorted(upstream_ids)}")
    if len(upstream_ids) < 2:
        print(
            f"[c1:forge] WARNING: expected ≥2 upstream products in consumes[]; "
            f"got {upstream_ids}",
            file=sys.stderr,
        )

    print(f"[c1:forge] ✅ contract written + validated at {result.contract_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
