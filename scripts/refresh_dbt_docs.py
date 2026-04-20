from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from local_env_utils import parse_env_file


@dataclass(frozen=True)
class ScenarioProject:
    key: str
    host_project_dir: str
    container_project_dir: str
    summary: str
    expected_models: tuple[str, ...]


REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = REPO_ROOT / ".env"
DOCS_OUTPUT_DIR = REPO_ROOT / "runtime" / "dbt-docs" / "site"


def load_env() -> dict[str, str]:
    values = parse_env_file(ENV_FILE)
    merged = dict(values)
    merged.update({key: value for key, value in os.environ.items() if value})
    return merged


def normalize_scenario(value: str) -> str:
    normalized = value.strip().lower()
    aliases = {
        "a1": "a1",
        "external": "a1",
        "external-reference": "a1",
        "a2": "a2",
        "internal": "a2",
        "internal-reference": "a2",
        "b1": "b1",
        "ai-external": "b1",
        "ai-reference-external": "b1",
        "b2": "b2",
        "ai-generated": "b2",
        "ai-generate-in-workspace": "b2",
    }
    if normalized not in aliases:
        raise ValueError(f"Unsupported scenario {value!r}. Use one of: A1, A2, B1, B2.")
    return aliases[normalized]


def resolve_scenario(scenario: str, env: dict[str, str]) -> ScenarioProject:
    greenfield = env.get("FLUID_DEMO_GITLAB_WORKSPACE", "").strip()
    existing = env.get("FLUID_AI_GITLAB_WORKSPACE", "").strip()

    if scenario in {"a1", "a2", "b1"} and not greenfield:
        raise RuntimeError("FLUID_DEMO_GITLAB_WORKSPACE is missing in .env or the current shell.")
    if scenario == "b2" and not existing:
        raise RuntimeError("FLUID_AI_GITLAB_WORKSPACE is missing in .env or the current shell.")

    projects = {
        "a1": ScenarioProject(
            key="A1",
            host_project_dir=f"{greenfield}/reference-assets/dbt_dv2_subscriber360",
            container_project_dir="/workspace/greenfield/reference-assets/dbt_dv2_subscriber360",
            summary="External-reference silver contract uses the shared DV2 project in Workspace A.",
            expected_models=("mart_subscriber360_core", "mart_subscriber_health_scorecard"),
        ),
        "a2": ScenarioProject(
            key="A2",
            host_project_dir=f"{greenfield}/variants/A2-internal-reference/dbt_dv2_subscriber360",
            container_project_dir="/workspace/greenfield/variants/A2-internal-reference/dbt_dv2_subscriber360",
            summary="Internal-reference silver contract uses the in-product DV2 project in Workspace A.",
            expected_models=("mart_subscriber360_core", "mart_subscriber_health_scorecard"),
        ),
        "b1": ScenarioProject(
            key="B1",
            host_project_dir=f"{greenfield}/reference-assets/dbt_dv2_subscriber360",
            container_project_dir="/workspace/greenfield/reference-assets/dbt_dv2_subscriber360",
            summary="AI external-reference flow reuses the shared DV2 project from Workspace A.",
            expected_models=("mart_subscriber360_core", "mart_subscriber_health_scorecard"),
        ),
        "b2": ScenarioProject(
            key="B2",
            host_project_dir=f"{existing}/variants/B2-ai-generate-in-workspace/subscriber360-generated/generated/dbt",
            container_project_dir="/workspace/import/variants/B2-ai-generate-in-workspace/subscriber360-generated/generated/dbt",
            summary="AI generated-assets flow uses the generated DV2 project in Workspace B.",
            expected_models=("mart_subscriber360_core", "mart_subscriber_health_scorecard"),
        ),
    }
    return projects[scenario]


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def wait_for_docs(url: str, timeout_seconds: float = 20.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.5)
            continue
        time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for dbt docs at {url}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Refresh the local dbt docs site for a telco silver demo scenario."
    )
    parser.add_argument("--scenario", required=True, help="Scenario selector: A1, A2, B1, or B2.")
    args = parser.parse_args()

    scenario = normalize_scenario(args.scenario)
    env = load_env()
    project = resolve_scenario(scenario, env)
    host_project = Path(project.host_project_dir).expanduser().resolve()

    if not host_project.exists():
        raise FileNotFoundError(
            f"Expected dbt project for scenario {project.key} at {host_project}. "
            "Create or generate that scenario first."
        )

    shutil.rmtree(DOCS_OUTPUT_DIR, ignore_errors=True)
    DOCS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    base = [
        "docker",
        "compose",
        "-f",
        str(REPO_ROOT / "deploy" / "docker" / "docker-compose.yml"),
        "--env-file",
        str(ENV_FILE),
        "exec",
        "-T",
        "dbt-runner",
        "dbt",
    ]

    common_args = [
        "--project-dir",
        project.container_project_dir,
        "--profiles-dir",
        "/opt/project/config/dbt",
        "--profile",
        "telco",
    ]

    run(base + ["parse"] + common_args)
    run(base + ["compile"] + common_args)
    run(
        base
        + [
            "docs",
            "generate",
            *common_args,
            "--target-path",
            "/opt/project/runtime/dbt-docs/site",
        ]
    )

    dbt_docs_port = env.get("DBT_DOCS_PORT", "8086")
    docs_url = f"http://localhost:{dbt_docs_port}/catalog.json"
    run(
        [
            "docker",
            "compose",
            "-f",
            str(REPO_ROOT / "deploy" / "docker" / "docker-compose.yml"),
            "--env-file",
            str(ENV_FILE),
            "restart",
            "dbt-docs",
        ]
    )
    wait_for_docs(docs_url)

    print(f"Refreshed dbt docs for scenario {project.key}.")
    print(project.summary)
    print(f"Project root: {host_project}")
    print(f"dbt docs UI: http://localhost:{dbt_docs_port}")
    print("Expected core models:")
    for model in project.expected_models:
        print(f"  - {model}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - CLI failure path
        print(str(exc), file=sys.stderr)
        sys.exit(1)
