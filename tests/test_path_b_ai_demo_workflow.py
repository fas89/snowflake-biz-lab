"""Lab-side pin tests for the Path B + C AI-forge demos.

These tests load the post-forge contracts straight from the lab's
working tree (or freshly-rendered output dirs) and assert the shape
that the demo relies on. They do NOT touch forge-cli code — every
assertion reads YAML via PyYAML.

Coverage:

* **B1** — schema, productType=ADP, hybrid-reference + dbt repository
  pin, provenance labels.
* **B2** — same as B1 + ``builds[*].repository`` points at
  in-workspace dbt + ``provenance.aiContributions`` mentions
  contract,dbt,airflow,jenkinsfile.
* **C1** — productType=CDP, ``consumes[]`` lists both B1 and B2's
  product IDs, ``provenance.composedFrom: B1+B2``.
* **PII propagation** — when a B1 expose has ``sensitivity: pii`` on
  a column, C1 has the same tag on the matching downstream column.
* **Live + golden parity** — every scenario must validate cleanly
  via ``fluid validate`` regardless of whether AI forged it live or
  was copied from the golden fixture.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PATH_B = REPO_ROOT / "gitlab" / "path-b-ai-telco-silver-import-demo" / "variants"

B1_CONTRACT = (
    PATH_B / "B1-ai-reference-external" / "subscriber360-external" /
    "contract.fluid.yaml"
)
B2_CONTRACT = (
    PATH_B / "B2-ai-generate-in-workspace" / "subscriber360-generated" /
    "contract.fluid.yaml"
)
C1_CONTRACT = (
    PATH_B / "C1-compose-cdp" / "customer_360_cdp" / "contract.fluid.yaml"
)
GOLDEN = REPO_ROOT / "fluid" / "fixtures" / "forge-golden"


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


# ---------------------------------------------------------------------------
# B1 contract shape.
# ---------------------------------------------------------------------------


class TestB1ContractShape:
    """B1 = AI-forged silver ADP that references the shared Path-A dbt
    project. The forge call + lab hardening together must produce
    these invariants."""

    @pytest.fixture(scope="class")
    def doc(self) -> dict:
        if not B1_CONTRACT.exists():
            pytest.skip(f"B1 contract not present at {B1_CONTRACT}")
        return _load_yaml(B1_CONTRACT)

    def test_metadata_layer_silver(self, doc):
        assert doc.get("metadata", {}).get("layer") == "Silver"

    def test_metadata_product_type_adp(self, doc):
        assert doc.get("metadata", {}).get("productType") == "ADP"

    def test_fluid_version_073(self, doc):
        assert doc.get("fluidVersion") == "0.7.3"

    def test_builds_pattern_hybrid_reference(self, doc):
        builds = doc.get("builds") or []
        assert builds, "B1 must declare at least one build"
        for b in builds:
            assert b.get("pattern") == "hybrid-reference", (
                "B1 references the external dbt project — every build must be "
                f"hybrid-reference, got {b.get('pattern')!r}"
            )

    def test_provenance_labels_present(self, doc):
        labels = doc.get("labels") or {}
        for key in (
            "provenance.scenario",
            "provenance.aiMode",
            "provenance.aiProvider",
            "provenance.aiModel",
        ):
            assert key in labels, f"missing provenance label {key!r}"


# ---------------------------------------------------------------------------
# B2 contract shape — staged pipeline + in-workspace assets.
# ---------------------------------------------------------------------------


class TestB2ContractShape:

    @pytest.fixture(scope="class")
    def doc(self) -> dict:
        if not B2_CONTRACT.exists():
            pytest.skip(f"B2 contract not present at {B2_CONTRACT}")
        return _load_yaml(B2_CONTRACT)

    def test_metadata_layer_silver_product_type_adp(self, doc):
        assert doc.get("metadata", {}).get("layer") == "Silver"
        assert doc.get("metadata", {}).get("productType") == "ADP"

    def test_builds_in_workspace_dbt(self, doc):
        """B2 generates dbt in-workspace; the build's repository
        should point at ``./generated/...`` not at the external Path-A
        reference."""
        builds = doc.get("builds") or []
        for b in builds:
            repo = b.get("repository") or ""
            assert (
                repo.startswith("./generated/") or repo.startswith("generated/")
            ), (
                f"B2 build repository should be in-workspace; got {repo!r}"
            )

    def test_ai_contributions_label_full_stack(self, doc):
        """Provenance label tracks exactly what AI authored."""
        labels = doc.get("labels") or {}
        contributions = labels.get("provenance.aiContributions", "")
        for kind in ("contract", "dbt", "airflow", "jenkinsfile"):
            assert kind in contributions, (
                f"provenance.aiContributions should include {kind!r}; "
                f"got {contributions!r}"
            )


# ---------------------------------------------------------------------------
# C1 — composition shape + PII propagation.
# ---------------------------------------------------------------------------


class TestC1Composition:

    @pytest.fixture(scope="class")
    def doc(self) -> dict:
        if not C1_CONTRACT.exists():
            pytest.skip(f"C1 contract not present at {C1_CONTRACT}")
        return _load_yaml(C1_CONTRACT)

    def test_metadata_layer_gold_product_type_cdp(self, doc):
        assert doc.get("metadata", {}).get("layer") == "Gold"
        assert doc.get("metadata", {}).get("productType") == "CDP"

    def test_consumes_includes_both_upstream_products(self, doc):
        consumes = doc.get("consumes") or []
        upstream_ids = {c.get("productId") for c in consumes if isinstance(c, dict)}
        # B1 and B2 contracts (both AI-forged silver products).
        b1_id = "silver.telco.subscriber360_ai_external_v1"
        b2_id = "silver.telco.subscriber360_ai_generated_v1"
        assert b1_id in upstream_ids, (
            f"C1 must consume from B1 ({b1_id}); got {upstream_ids}"
        )
        assert b2_id in upstream_ids, (
            f"C1 must consume from B2 ({b2_id}); got {upstream_ids}"
        )

    def test_provenance_composed_from_b1_b2(self, doc):
        labels = doc.get("labels") or {}
        composed = labels.get("provenance.composedFrom") or labels.get("c1ComposedFrom")
        assert composed == "B1+B2", (
            f"provenance.composedFrom should be 'B1+B2'; got {composed!r}"
        )

    def test_pii_propagation_from_upstream_to_c1(self, doc):
        """When B1's subscriber360_core has ACCOUNT_NUMBER tagged
        ``sensitivity: pii``, the same column in C1 should inherit
        the tag (lab-stub stamps it; the live forge propagates via
        propagate_pii_classifications)."""
        # Find ACCOUNT_NUMBER in C1's first expose schema
        for expose in doc.get("exposes") or []:
            schema = (expose.get("contract") or {}).get("schema") or []
            for col in schema:
                if col.get("name") == "ACCOUNT_NUMBER":
                    assert col.get("sensitivity") == "pii", (
                        "C1.exposes[].schema.ACCOUNT_NUMBER should inherit "
                        "PII tag from upstream B1.subscriber360_core."
                    )
                    return
        pytest.fail("C1 contract missing ACCOUNT_NUMBER column")


# ---------------------------------------------------------------------------
# Live + golden parity — every scenario validates via fluid validate.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name,path",
    [
        ("B1", B1_CONTRACT),
        ("B2", B2_CONTRACT),
        ("C1", C1_CONTRACT),
    ],
)
def test_contract_validates_cleanly(name, path):
    """Every demo contract must pass `fluid validate` — regardless of
    whether AI forged it live or it came from a golden fixture.

    The fluid CLI is resolved from ``.venv.fluid-dev/bin/fluid`` if
    present (the dev-source venv) so this test is hermetic to the
    user's PATH.
    """
    if not path.exists():
        pytest.skip(f"{name} contract not present at {path}")
    fluid_bin = REPO_ROOT / ".venv.fluid-dev" / "bin" / "fluid"
    if not fluid_bin.exists():
        # Fallback: forge-cli sibling repo.
        sibling = REPO_ROOT.parent / "forge-cli" / ".venv" / "bin" / "python"
        if not sibling.exists():
            pytest.skip("fluid CLI not reachable from either lab .venv or sibling forge-cli")
        proc = subprocess.run(
            [str(sibling), "-m", "fluid_build.cli", "validate", str(path)],
            capture_output=True,
            text=True,
        )
    else:
        proc = subprocess.run(
            [str(fluid_bin), "validate", str(path)],
            capture_output=True,
            text=True,
        )
    assert proc.returncode == 0, (
        f"{name} contract failed validation: {proc.stdout}\n{proc.stderr}"
    )


# ---------------------------------------------------------------------------
# Golden fixtures present and parseable.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "scenario",
    ["B1-ai-reference-external", "B2-ai-generate-in-workspace", "C1-compose-cdp"],
)
def test_golden_fixture_present_and_parseable(scenario):
    """Every demo scenario must have a golden fixture so the
    ``FLUID_LIVE_AI=0`` path keeps the demo runnable in offline / CI
    / no-budget contexts."""
    p = GOLDEN / scenario / "contract.fluid.yaml"
    assert p.exists(), f"golden fixture missing for {scenario} at {p}"
    doc = _load_yaml(p)
    assert doc.get("fluidVersion"), f"{scenario} golden missing fluidVersion"
    assert doc.get("id"), f"{scenario} golden missing id"
