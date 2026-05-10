"""B1 — AI-forged silver Subscriber 360 (external dbt reference).

What the script does end-to-end:

1. **Live AI step** — drives the forge-cli staged copilot pipeline
   (LogicalAgent → BuilderAgent → ReadmeAgent / TransformationAgent →
   ValidatorAgent → ConformanceAgent) via ``fluid forge --copilot
   --data-product-type ADP --domain telco``. The staged pipeline
   proposes:
     - schema with the right SDP/ADP/CDP shape
     - ``semantics`` block (entities, measures, metrics)
     - ``dq.rules`` (completeness, accuracy)
     - ``policy.classification`` + per-column ``sensitivity`` (PII)
   Self-heals up to 3 attempts when ValidatorAgent finds drift.

2. **Lab hardening** — applies deterministic post-AI fixes that the
   ML pipeline can't reliably emit:
     - ``metadata.layer: Silver`` + ``metadata.productType: ADP``
       (required by SDP/ADP/CDP equivalence axiom)
     - ``builds[*].pattern: hybrid-reference`` (B1 owns the
       contract; external dbt project owns materialisation)
     - ``builds[*].repository`` pointing at
       ``../../reference-assets/dbt_dv2_subscriber360`` so the
       contract resolves the shared DV2 project
     - ``provenance.*`` labels capturing scenario / mode / model

3. **Fallback** — if ``FLUID_LIVE_AI=0`` or no API key is set, the
   golden fixture from
   ``fluid/fixtures/forge-golden/B1-ai-reference-external/`` is
   copied in place, lab hardening is still applied. This keeps the
   demo runnable in offline / CI / no-budget mode.

The Jenkinsfile is intentionally NOT regenerated — the existing one
already carries the recent forge-cli ``--mode "$APPLY_MODE"`` fix
and lab-specific tweaks (`subscriber360-external` workdir, dev-source
install). Re-running ``fluid generate ci`` would clobber those.

Usage:

  # Live (default)
  task b1:forge

  # Force golden replay
  FLUID_LIVE_AI=0 task b1:forge

  # Pin a specific provider
  LITELLM_PROVIDER=openai task b1:forge
"""

# ruff: noqa: T201  # CLI scripts intentionally print to stdout for the operator.

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml

# Local helper
sys.path.insert(0, str(Path(__file__).parent))
from _ai_forge_common import (  # noqa: E402
    REPO_ROOT,
    run_forge_with_fallback,
    stamp_provenance_label,
)

SCENARIO = "B1-ai-reference-external"
TARGET_REL = (
    "gitlab/path-b-ai-telco-silver-import-demo/variants/"
    "B1-ai-reference-external/subscriber360-external"
)
DBT_PROJECT_REL = "../../reference-assets/dbt_dv2_subscriber360"


def harden_b1_contract(contract_path: Path) -> None:
    """Apply B1-specific lab guardrails to the AI-emitted contract.

    Idempotent: running multiple times converges to the same result.
    """
    doc = yaml.safe_load(contract_path.read_text(encoding="utf-8")) or {}

    # SDP/ADP/CDP equivalence axiom: B1 is silver/ADP.
    metadata = doc.setdefault("metadata", {})
    metadata.setdefault("layer", "Silver")
    metadata.setdefault("productType", "ADP")

    # ``hybrid-reference`` pattern + repository pin so apply provisions
    # only the schema; the external dbt project owns materialisation.
    builds = doc.get("builds")
    if isinstance(builds, list):
        for b in builds:
            if not isinstance(b, dict):
                continue
            b.setdefault("pattern", "hybrid-reference")
            b.setdefault("engine", "dbt")
            b.setdefault("repository", DBT_PROJECT_REL)

    # Bump fluidVersion to 0.7.3 if the AI emitted an older version.
    if doc.get("fluidVersion", "0.7.2") < "0.7.3":
        doc["fluidVersion"] = "0.7.3"

    contract_path.write_text(
        yaml.safe_dump(doc, sort_keys=False), encoding="utf-8"
    )


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Drive the B1 AI forge cycle.")
    p.add_argument(
        "--target-dir",
        default=str(REPO_ROOT / TARGET_REL),
        help="Where to write the contract + assets (default: B1 variant tree).",
    )
    p.add_argument(
        "--fluid-bin",
        default=str(REPO_ROOT / ".venv.fluid-dev/bin/fluid"),
        help="Path to the fluid CLI binary (dev-source venv by default).",
    )
    args = p.parse_args(argv)

    target_dir = Path(args.target_dir).resolve()
    fluid_bin = Path(args.fluid_bin).resolve()
    if not fluid_bin.exists():
        print(
            f"[b1:forge] FATAL: fluid CLI not found at {fluid_bin}. "
            "Run `task fluid:bootstrap:dev` first.",
            file=sys.stderr,
        )
        return 2

    print(f"[b1:forge] scenario={SCENARIO}")
    print(f"[b1:forge] target_dir={target_dir}")

    result = run_forge_with_fallback(
        scenario=SCENARIO,
        target_dir=target_dir,
        fluid_bin=fluid_bin,
        data_product_type="ADP",
        domain="telco",
        # Don't pass --from-product — B1 is a fresh ADP authored from
        # the seeded telco bronze. The MCP discovery + LogicalAgent
        # do the upstream binding themselves.
        extra_argv=None,
        env=os.environ.copy(),
    )

    print(
        f"[b1:forge] mode={result.mode} provider={result.provider.provider} "
        f"model={result.provider.model} rc={result.rc}"
    )
    if result.receipt_dir:
        try:
            rel = result.receipt_dir.relative_to(REPO_ROOT)
        except ValueError:
            rel = result.receipt_dir
        print(f"[b1:forge] receipt: {rel}")

    if not result.contract_path.exists():
        print(
            f"[b1:forge] FATAL: contract not found at {result.contract_path}",
            file=sys.stderr,
        )
        return 1

    # Lab hardening — applies regardless of live/golden mode.
    harden_b1_contract(result.contract_path)
    stamp_provenance_label(
        result.contract_path,
        scenario=SCENARIO,
        mode=result.mode,
        provider=result.provider,
        receipt_dir=result.receipt_dir,
    )

    # Validate the post-hardening contract via fluid validate.
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

    print(f"[b1:forge] ✅ contract written + validated at {result.contract_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
