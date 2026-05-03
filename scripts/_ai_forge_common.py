"""Shared scaffolding for the live-AI forge demos (B1, B2, C1).

This helper centralises three pieces every Path B / Path C scenario
needs:

1. **Provider selection** — Gemini (primary, default) and OpenAI
   (alternate). Anthropic is intentionally NOT supported on this
   path; the lab is licensed for Gemini + OpenAI only.

2. **Live-vs-golden dispatch** — when ``FLUID_LIVE_AI=1`` (default)
   AND a usable API key is set in the env, we invoke
   ``fluid forge --copilot ...`` for real. Otherwise we copy the
   deterministic golden fixture from
   ``fluid/fixtures/forge-golden/<scenario>/`` so the demo still
   works offline / on CI runners without keys.

3. **Receipt capture** — every successful live run writes a
   timestamped snapshot (raw contract, log, env summary) under
   ``runtime/generated/forge-receipts/<scenario>/<UTC-timestamp>/``
   so operators can replay or diff.

The dispatcher is intentionally side-effect-light: it returns
structured info (live? path? receipt?) rather than mutating global
state, so each scenario script can compose it with its own
post-forge hardening (uppercase fix, productType stamp, label
provenance).
"""

# ruff: noqa: T201  # CLI scripts intentionally print to stdout for the operator.

from __future__ import annotations

import datetime as _dt
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_ROOT = REPO_ROOT / "fluid" / "fixtures" / "forge-golden"
RECEIPTS_ROOT = REPO_ROOT / "runtime" / "generated" / "forge-receipts"


# ---------------------------------------------------------------------------
# Provider selection — Gemini default, OpenAI alternate, Anthropic excluded.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LlmProviderChoice:
    """Resolved LiteLLM provider config for a single forge run."""

    provider: str  # "gemini" | "openai"
    model: str
    api_key_env_var: str  # e.g. "GEMINI_API_KEY"
    api_key_present: bool


def resolve_llm_provider(env: Optional[Dict[str, str]] = None) -> LlmProviderChoice:
    """Pick the live-LLM provider for this run.

    Lookup order (first match wins):

    1. Explicit operator override via ``LITELLM_PROVIDER`` (must be
       ``gemini`` or ``openai`` — Anthropic is rejected with a clear
       error).
    2. ``GEMINI_API_KEY`` is set → Gemini (default; cheapest).
    3. ``OPENAI_API_KEY`` is set → OpenAI (alternate; supports
       ``FLUID_OPENAI_STRICT_SCHEMA=1``).
    4. Neither key present → return a Gemini placeholder with
       ``api_key_present=False`` so the dispatcher knows to fall
       back to the golden fixture.
    """
    e = env if env is not None else os.environ

    # Explicit override
    requested = (e.get("LITELLM_PROVIDER") or "").strip().lower()
    if requested == "anthropic":
        raise ValueError(
            "Anthropic is not on the supported provider list for the "
            "snowflake-biz-lab AI demos. Use LITELLM_PROVIDER=gemini "
            "(default) or LITELLM_PROVIDER=openai. Update LITELLM_PROVIDER "
            "in your .env or unset it."
        )
    if requested == "openai":
        return LlmProviderChoice(
            provider="openai",
            model=(e.get("LITELLM_MODEL") or "gpt-4o-mini"),
            api_key_env_var="OPENAI_API_KEY",
            api_key_present=bool(e.get("OPENAI_API_KEY", "").strip()),
        )
    if requested == "gemini":
        return LlmProviderChoice(
            provider="gemini",
            model=(e.get("LITELLM_MODEL") or "gemini-2.5-flash"),
            api_key_env_var="GEMINI_API_KEY",
            api_key_present=bool(e.get("GEMINI_API_KEY", "").strip()),
        )

    # Auto-pick: Gemini > OpenAI
    if e.get("GEMINI_API_KEY", "").strip():
        return LlmProviderChoice(
            provider="gemini",
            model=(e.get("LITELLM_MODEL") or "gemini-2.5-flash"),
            api_key_env_var="GEMINI_API_KEY",
            api_key_present=True,
        )
    if e.get("OPENAI_API_KEY", "").strip():
        return LlmProviderChoice(
            provider="openai",
            model=(e.get("LITELLM_MODEL") or "gpt-4o-mini"),
            api_key_env_var="OPENAI_API_KEY",
            api_key_present=True,
        )
    # Neither present
    return LlmProviderChoice(
        provider="gemini",
        model="gemini-2.5-flash",
        api_key_env_var="GEMINI_API_KEY",
        api_key_present=False,
    )


# ---------------------------------------------------------------------------
# Live-vs-golden dispatcher.
# ---------------------------------------------------------------------------


@dataclass
class ForgeRunResult:
    """Outcome of a single forge invocation (live or golden)."""

    scenario: str
    mode: str  # "live" | "golden" | "live-failed-fallback"
    contract_path: Path
    receipt_dir: Optional[Path] = None
    rc: int = 0
    stderr_excerpt: str = ""
    provider: Optional[LlmProviderChoice] = None
    extra: Dict[str, Any] = field(default_factory=dict)


def is_live_ai_enabled(env: Optional[Dict[str, str]] = None) -> bool:
    """``FLUID_LIVE_AI=1`` (default) → live; ``=0`` / ``=false`` → golden."""
    e = env if env is not None else os.environ
    raw = (e.get("FLUID_LIVE_AI", "1") or "").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def make_receipt_dir(scenario: str) -> Path:
    """``runtime/generated/forge-receipts/<scenario>/<UTC-timestamp>/``"""
    p = RECEIPTS_ROOT / scenario / _utc_stamp()
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_receipt_metadata(
    receipt_dir: Path,
    *,
    scenario: str,
    mode: str,
    provider: Optional[LlmProviderChoice],
    forge_argv: List[str],
    rc: int,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Drop a JSON receipt summarising the run."""
    payload: Dict[str, Any] = {
        "scenario": scenario,
        "mode": mode,
        "timestamp_utc": _utc_stamp(),
        "rc": rc,
        "forge_argv_redacted": [a for a in forge_argv if "API_KEY" not in a.upper()],
    }
    if provider is not None:
        payload["provider"] = {
            "provider": provider.provider,
            "model": provider.model,
            "api_key_env_var": provider.api_key_env_var,
            "api_key_present": provider.api_key_present,
        }
    if extra:
        payload["extra"] = extra
    (receipt_dir / "receipt.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )


def copy_golden(
    scenario: str,
    *,
    target_dir: Path,
    files: Optional[List[str]] = None,
) -> Path:
    """Copy from ``fluid/fixtures/forge-golden/<scenario>/`` to *target_dir*.

    ``files`` lets the caller request a subset (e.g. only the
    ``contract.fluid.yaml``); when ``None`` the entire scenario tree
    is mirrored. Returns the path to ``contract.fluid.yaml`` after
    the copy so callers can stamp post-fix labels into it.
    """
    src = GOLDEN_ROOT / scenario
    if not src.exists():
        raise FileNotFoundError(
            f"Golden fixture missing for scenario {scenario!r} at {src}. "
            "Either set FLUID_LIVE_AI=1 + a valid GEMINI_API_KEY/OPENAI_API_KEY "
            "OR run `task <scenario>:freeze-golden` first."
        )
    target_dir.mkdir(parents=True, exist_ok=True)
    if files is None:
        # Mirror full tree (skipping README.md so the lab readme stays
        # operator-authored, not a copy of the golden's).
        for entry in src.iterdir():
            if entry.name == "README.md":
                continue
            dst = target_dir / entry.name
            if entry.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(entry, dst)
            else:
                shutil.copy2(entry, dst)
    else:
        for rel in files:
            s = src / rel
            d = target_dir / rel
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, d)
    return target_dir / "contract.fluid.yaml"


def invoke_fluid_forge(
    *,
    fluid_bin: Path,
    target_dir: Path,
    data_product_type: str,
    domain: str,
    extra_argv: Optional[List[str]] = None,
    provider: LlmProviderChoice,
    env_passthrough: Dict[str, str],
    capture_log: Optional[Path] = None,
    timeout_sec: int = 600,
) -> tuple[int, str]:
    """Invoke ``fluid forge --copilot ...`` for a live run.

    Returns ``(rc, stderr_excerpt)``. ``capture_log`` (when set) gets
    the full combined stdout+stderr stream for the receipt directory.
    Sets the LiteLLM env vars to pin Gemini or OpenAI per the resolved
    provider.
    """
    argv: List[str] = [
        str(fluid_bin),
        "forge",
        "--copilot",
        "--target-dir",
        str(target_dir),
        "--data-product-type",
        data_product_type,
        "--domain",
        domain,
        # Yes-to-all so the demo never hangs at a confirm prompt.
        "--yes",
    ]
    if extra_argv:
        argv.extend(extra_argv)

    run_env = dict(env_passthrough)
    run_env.setdefault("FLUID_LLM_BACKEND", "litellm")
    run_env["LITELLM_PROVIDER"] = provider.provider
    run_env["LITELLM_MODEL"] = provider.model
    # Default cost ceiling so a runaway forge doesn't burn the lab budget.
    run_env.setdefault("FLUID_COST_LIMIT_USD_PER_PRODUCT", "0.50")

    try:
        proc = subprocess.run(
            argv,
            env=run_env,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
    except subprocess.TimeoutExpired:
        if capture_log is not None:
            capture_log.write_text(
                f"TIMEOUT after {timeout_sec}s\n", encoding="utf-8"
            )
        return 124, f"timeout after {timeout_sec}s"

    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if capture_log is not None:
        capture_log.write_text(combined, encoding="utf-8")
    excerpt_lines = (proc.stderr or "").splitlines()[-30:]
    return proc.returncode, "\n".join(excerpt_lines)


def run_forge_with_fallback(
    *,
    scenario: str,
    target_dir: Path,
    fluid_bin: Path,
    data_product_type: str,
    domain: str,
    extra_argv: Optional[List[str]] = None,
    env: Optional[Dict[str, str]] = None,
) -> ForgeRunResult:
    """Top-level entry: live forge, fall back to golden on failure / opt-out.

    The decision tree:

    * ``FLUID_LIVE_AI`` opt-out OR no API key OR no LiteLLM backend
      configured → straight to golden, mode=``"golden"``.
    * Live invocation succeeds (rc=0 + contract written) →
      mode=``"live"``.
    * Live invocation fails → mode=``"live-failed-fallback"``, golden
      is copied over, stderr excerpt preserved in the receipt.
    """
    e = env if env is not None else os.environ
    receipt = make_receipt_dir(scenario)
    provider = resolve_llm_provider(e)

    if not is_live_ai_enabled(e) or not provider.api_key_present:
        contract = copy_golden(scenario, target_dir=target_dir)
        write_receipt_metadata(
            receipt,
            scenario=scenario,
            mode="golden",
            provider=provider,
            forge_argv=[],
            rc=0,
            extra={
                "reason": (
                    "FLUID_LIVE_AI=0"
                    if not is_live_ai_enabled(e)
                    else f"missing {provider.api_key_env_var}"
                )
            },
        )
        return ForgeRunResult(
            scenario=scenario,
            mode="golden",
            contract_path=contract,
            receipt_dir=receipt,
            rc=0,
            provider=provider,
        )

    target_dir.mkdir(parents=True, exist_ok=True)
    log = receipt / "forge.log"
    rc, stderr_excerpt = invoke_fluid_forge(
        fluid_bin=fluid_bin,
        target_dir=target_dir,
        data_product_type=data_product_type,
        domain=domain,
        extra_argv=extra_argv,
        provider=provider,
        env_passthrough=e,
        capture_log=log,
    )

    contract = target_dir / "contract.fluid.yaml"
    if rc == 0 and contract.exists():
        write_receipt_metadata(
            receipt,
            scenario=scenario,
            mode="live",
            provider=provider,
            forge_argv=["fluid", "forge", "--copilot", "--data-product-type",
                        data_product_type, "--domain", domain],
            rc=0,
        )
        return ForgeRunResult(
            scenario=scenario,
            mode="live",
            contract_path=contract,
            receipt_dir=receipt,
            rc=0,
            provider=provider,
        )

    # Live failed — fall back to golden so the rest of the demo still runs.
    print(
        f"[forge:{scenario}] live forge failed (rc={rc}); falling back to "
        f"golden fixture. stderr tail:\n{stderr_excerpt}",
        file=sys.stderr,
    )
    contract = copy_golden(scenario, target_dir=target_dir)
    write_receipt_metadata(
        receipt,
        scenario=scenario,
        mode="live-failed-fallback",
        provider=provider,
        forge_argv=["fluid", "forge", "--copilot", "--data-product-type",
                    data_product_type, "--domain", domain],
        rc=rc,
        extra={"stderr_excerpt": stderr_excerpt},
    )
    return ForgeRunResult(
        scenario=scenario,
        mode="live-failed-fallback",
        contract_path=contract,
        receipt_dir=receipt,
        rc=rc,
        stderr_excerpt=stderr_excerpt,
        provider=provider,
    )


# ---------------------------------------------------------------------------
# Post-forge hardening helpers — every scenario applies these after the
# AI-or-golden contract lands so the demo is reproducible.
# ---------------------------------------------------------------------------


def stamp_provenance_label(
    contract_path: Path,
    *,
    scenario: str,
    mode: str,
    provider: LlmProviderChoice,
    receipt_dir: Optional[Path],
) -> None:
    """Stamp ``labels.provenance.*`` keys on the contract so downstream
    audit (DMM publish, receipts) carries the AI surface.

    Schema-compatible — top-level ``labels`` is open under the v0.7.x
    schema (additionalProperties allows scalar strings).
    """
    import yaml as _yaml

    doc = _yaml.safe_load(contract_path.read_text(encoding="utf-8")) or {}
    labels = doc.setdefault("labels", {})
    if not isinstance(labels, dict):
        labels = {}
        doc["labels"] = labels
    labels["provenance.scenario"] = scenario
    labels["provenance.aiMode"] = mode
    labels["provenance.aiProvider"] = provider.provider
    labels["provenance.aiModel"] = provider.model
    if receipt_dir is not None:
        try:
            rel = receipt_dir.relative_to(REPO_ROOT)
            labels["provenance.aiReceipt"] = str(rel)
        except ValueError:
            labels["provenance.aiReceipt"] = str(receipt_dir)
    contract_path.write_text(
        _yaml.safe_dump(doc, sort_keys=False), encoding="utf-8"
    )


__all__ = [
    "ForgeRunResult",
    "GOLDEN_ROOT",
    "LlmProviderChoice",
    "RECEIPTS_ROOT",
    "REPO_ROOT",
    "copy_golden",
    "invoke_fluid_forge",
    "is_live_ai_enabled",
    "make_receipt_dir",
    "resolve_llm_provider",
    "run_forge_with_fallback",
    "stamp_provenance_label",
    "write_receipt_metadata",
]
