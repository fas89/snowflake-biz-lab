"""B2 — MCP-discovered, AI-generated silver Subscriber 360 in-workspace.

What B2 demonstrates that B1 doesn't:

* **Staged multi-agent copilot** — drives the StageCoordinator
  pipeline (LogicalAgent → BuilderAgent + ReadmeAgent +
  TransformationAgent in parallel → ValidatorAgent →
  ConformanceAgent), with self-healing repair loops up to 3
  attempts when ValidatorAgent finds drift.
* **Generated assets in workspace** — emits dbt project + Airflow
  DAG into ``./generated/`` alongside the contract, so the demo
  shows AI-authored *runnable* assets, not just a contract that
  references external code.
* **Telco specialty** — ``--domain telco`` brings in TM Forum SID
  patterns, DV2 hub/sat hints, subscriber-360 mart shape from
  ``agent_specs/telco.yaml``.
* **MCP-driven discovery** — the staged pipeline's first call into
  forge-cli MCP introspects live Snowflake metadata
  (``TELCO_LAB.TELCO_STAGE_LOAD``) for table list, column types, PII
  tags, and downstream lineage hints.

Lab hardening (post-AI):

* ``metadata.layer: Silver`` + ``metadata.productType: ADP``.
* Move provenance under ``labels.provenance.*`` (schema-compatible
  audit trail).
* Bump ``fluidVersion`` to 0.7.3 if the AI emits an older version.
* Stamp ``provenance.aiContributions: contract,dbt,airflow,jenkinsfile``
  so the operator can see exactly what AI authored.

Generated tree under ``subscriber360-generated/``:

  contract.fluid.yaml        ← AI (with semantics, dq, policy)
  generated/
    dbt/
      dbt_project.yml        ← AI
      models/
        silver_subscriber360_core.sql                    ← AI
        silver_subscriber_health_scorecard.sql           ← AI
    airflow/
      silver_telco_subscriber360_ai_generated_v1_dag.py  ← AI
  Jenkinsfile                ← AI (via fluid generate ci)

Live mode default (Gemini 2.5 Flash); FLUID_LIVE_AI=0 falls back to
the golden fixture which already has all generated assets baked in.

Usage:

  task b2:forge
  FLUID_LIVE_AI=0 task b2:forge       # golden replay
  LITELLM_PROVIDER=openai task b2:forge
"""

# ruff: noqa: T201  # CLI scripts intentionally print to stdout for the operator.

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from _ai_forge_common import (  # noqa: E402
    GOLDEN_ROOT,
    REPO_ROOT,
    run_forge_with_fallback,
    stamp_provenance_label,
)

SCENARIO = "B2-ai-generate-in-workspace"
TARGET_REL = (
    "gitlab/path-b-ai-telco-silver-import-demo/variants/"
    "B2-ai-generate-in-workspace/subscriber360-generated"
)


def harden_b2_contract(contract_path: Path) -> None:
    """Apply B2-specific lab guardrails. Idempotent."""
    doc = yaml.safe_load(contract_path.read_text(encoding="utf-8")) or {}

    metadata = doc.setdefault("metadata", {})
    metadata.setdefault("layer", "Silver")
    metadata.setdefault("productType", "ADP")

    # B2's builds are in-workspace, not external.
    builds = doc.get("builds")
    if isinstance(builds, list):
        for b in builds:
            if not isinstance(b, dict):
                continue
            b.setdefault("pattern", "hybrid-reference")
            b.setdefault("engine", "dbt")
            b.setdefault("repository", "./generated/dbt/dbt_dv2_subscriber360")

    if doc.get("fluidVersion", "0.7.2") < "0.7.3":
        doc["fluidVersion"] = "0.7.3"

    contract_path.write_text(
        yaml.safe_dump(doc, sort_keys=False), encoding="utf-8"
    )


def _ensure_generated_assets_exist(target_dir: Path, scenario: str) -> None:
    """If the live forge didn't emit dbt/airflow assets under
    ``generated/``, copy them from the golden fixture.

    The staged copilot's BuilderAgent + TransformationAgent are
    expected to write these; this helper is the safety net for
    contract-only emit modes.
    """
    gen_target = target_dir / "generated"
    gen_golden = GOLDEN_ROOT / scenario / "generated"
    if not gen_golden.exists():
        return
    for kind in ("dbt", "airflow"):
        target_kind = gen_target / kind
        golden_kind = gen_golden / kind
        if not golden_kind.exists():
            continue
        if target_kind.exists() and any(target_kind.iterdir()):
            continue  # already populated
        if target_kind.exists():
            shutil.rmtree(target_kind)
        shutil.copytree(golden_kind, target_kind)


def _maybe_regenerate_jenkinsfile(
    *,
    target_dir: Path,
    fluid_bin: Path,
) -> None:
    """Regenerate the Jenkinsfile via ``fluid generate ci`` so it picks
    up the current forge-cli template (``--mode "$APPLY_MODE"`` on
    plan, security-scan stage on advanced complexity, etc.).

    Skips silently if ``fluid generate ci`` isn't reachable. The
    existing committed Jenkinsfile remains in place as a fallback.
    """
    jenkinsfile = target_dir / "Jenkinsfile"
    relpath = "variants/B2-ai-generate-in-workspace/subscriber360-generated"
    cmd = [
        str(fluid_bin),
        "generate",
        "ci",
        str(target_dir / "contract.fluid.yaml"),
        "--system",
        "jenkins",
        "--install-mode",
        "dev-source",
        "--complexity",
        "standard",
        "--default-publish-target",
        "datamesh-manager",
        "--out",
        str(jenkinsfile),
    ]
    print(f"[b2:forge] regenerating Jenkinsfile via: {' '.join(cmd[1:])}")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            print(
                f"[b2:forge] Jenkinsfile regen rc={proc.returncode}; "
                f"keeping existing file. stderr tail:\n{proc.stderr[-400:]}",
                file=sys.stderr,
            )
    except Exception as exc:  # noqa: BLE001
        print(f"[b2:forge] Jenkinsfile regen skipped: {exc}", file=sys.stderr)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Drive the B2 MCP+AI forge cycle.")
    p.add_argument("--target-dir", default=str(REPO_ROOT / TARGET_REL))
    p.add_argument(
        "--fluid-bin",
        default=str(REPO_ROOT / ".venv.fluid-dev/bin/fluid"),
    )
    p.add_argument(
        "--skip-jenkinsfile-regen",
        action="store_true",
        help="Don't re-run `fluid generate ci`; keep the committed Jenkinsfile.",
    )
    args = p.parse_args(argv)

    target_dir = Path(args.target_dir).resolve()
    fluid_bin = Path(args.fluid_bin).resolve()
    if not fluid_bin.exists():
        print(f"[b2:forge] FATAL: fluid CLI not found at {fluid_bin}", file=sys.stderr)
        return 2

    print(f"[b2:forge] scenario={SCENARIO}")
    print(f"[b2:forge] target_dir={target_dir}")

    # Force the staged copilot pipeline (default) — DON'T set
    # FLUID_FORGE_LEGACY_COPILOT, which would route to the legacy
    # single-shot path.
    forge_env = os.environ.copy()
    forge_env.pop("FLUID_FORGE_LEGACY_COPILOT", None)

    result = run_forge_with_fallback(
        scenario=SCENARIO,
        target_dir=target_dir,
        fluid_bin=fluid_bin,
        data_product_type="ADP",
        domain="telco",
        # MCP discovery + asset generation are driven by the staged
        # coordinator's BuilderAgent + TransformationAgent.
        extra_argv=None,
        env=forge_env,
    )

    print(
        f"[b2:forge] mode={result.mode} provider={result.provider.provider} "
        f"model={result.provider.model} rc={result.rc}"
    )
    if result.receipt_dir:
        try:
            rel = result.receipt_dir.relative_to(REPO_ROOT)
        except ValueError:
            rel = result.receipt_dir
        print(f"[b2:forge] receipt: {rel}")

    if not result.contract_path.exists():
        print("[b2:forge] FATAL: contract not found", file=sys.stderr)
        return 1

    harden_b2_contract(result.contract_path)
    stamp_provenance_label(
        result.contract_path,
        scenario=SCENARIO,
        mode=result.mode,
        provider=result.provider,
        receipt_dir=result.receipt_dir,
    )

    # Track aiContributions explicitly — B2 advertises full-stack AI.
    doc = yaml.safe_load(result.contract_path.read_text(encoding="utf-8"))
    labels = doc.setdefault("labels", {})
    labels["provenance.aiContributions"] = "contract,dbt,airflow,jenkinsfile"
    result.contract_path.write_text(
        yaml.safe_dump(doc, sort_keys=False), encoding="utf-8"
    )

    # Generated dbt + airflow assets (live forge writes them; golden
    # mode copies them from fixture).
    _ensure_generated_assets_exist(target_dir, SCENARIO)

    # Regenerate Jenkinsfile (optional — keeps the demo on the current
    # forge-cli template).
    if not args.skip_jenkinsfile_regen:
        _maybe_regenerate_jenkinsfile(target_dir=target_dir, fluid_bin=fluid_bin)

    # Validate the post-hardening contract.
    val = subprocess.run(
        [str(fluid_bin), "validate", str(result.contract_path)],
        capture_output=True,
        text=True,
    )
    print(val.stdout.splitlines()[-1] if val.stdout else "(no validate output)")
    if val.returncode != 0:
        print(val.stderr, file=sys.stderr)
        return 1

    # Sanity: confirm generated assets exist post-run.
    gen_dir = target_dir / "generated"
    has_dbt = (gen_dir / "dbt").is_dir() and any((gen_dir / "dbt").iterdir())
    has_airflow = (gen_dir / "airflow").is_dir() and any(
        (gen_dir / "airflow").iterdir()
    )
    has_jenkinsfile = (target_dir / "Jenkinsfile").exists()
    print(
        f"[b2:forge] generated_assets: dbt={has_dbt} airflow={has_airflow} "
        f"jenkinsfile={has_jenkinsfile}"
    )

    print(f"[b2:forge] ✅ contract written + validated at {result.contract_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
