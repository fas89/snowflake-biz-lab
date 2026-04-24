from __future__ import annotations

import argparse
import base64
import http.cookiejar
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from jenkins_param_defaults import has_install_overrides, jenkins_default_params
from local_env_utils import parse_env_file
from local_url_utils import validate_local_http_url


REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = REPO_ROOT / ".env"
JENKINS_ENV_FILE = REPO_ROOT / ".env.jenkins"
DEMO_RELEASE_ENV_FILE = REPO_ROOT / "runtime/generated/demo-release.env"


@dataclass(frozen=True)
class ScenarioConfig:
    scenario: str
    job_name: str
    default_params: tuple[tuple[str, str], ...] = ()


SCENARIOS: dict[str, ScenarioConfig] = {
    "A1": ScenarioConfig(
        scenario="A1",
        job_name="A1-external-reference",
        default_params=(("PUBLISH_TARGETS", "datamesh-manager"),),
    ),
    "A2": ScenarioConfig(
        scenario="A2",
        job_name="A2-internal-reference",
        default_params=(("PUBLISH_TARGETS", "datamesh-manager"),),
    ),
}


def load_env() -> dict[str, str]:
    merged = parse_env_file(ENV_FILE)
    merged.update(parse_env_file(DEMO_RELEASE_ENV_FILE))
    merged.update(parse_env_file(JENKINS_ENV_FILE))
    merged.update({key: value for key, value in os.environ.items() if value})
    return merged


def build_request(
    url: str,
    user: str,
    password: str,
    method: str = "GET",
    data: bytes | None = None,
    extra_headers: dict[str, str] | None = None,
) -> urllib.request.Request:
    token = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
    headers = {"Authorization": f"Basic {token}"}
    if extra_headers:
        headers.update(extra_headers)
    return urllib.request.Request(url, data=data, headers=headers, method=method)


def open_request(
    opener: urllib.request.OpenerDirector, request: urllib.request.Request
) -> urllib.response.addinfourl:
    return opener.open(request)


def fetch_crumb(
    opener: urllib.request.OpenerDirector,
    base_url: str,
    user: str,
    password: str,
) -> dict[str, str]:
    crumb_url = (
        base_url
        + "/crumbIssuer/api/xml?xpath="
        + urllib.parse.quote('concat(//crumbRequestField,":",//crumb)')
    )
    request = build_request(crumb_url, user, password)
    try:
        with open_request(opener, request) as response:
            payload = response.read().decode("utf-8").strip()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {}
        raise

    header, _, value = payload.partition(":")
    if not header or not value:
        raise RuntimeError(f"Unexpected crumb response from Jenkins: {payload!r}")
    return {header: value}


def job_exists(
    opener: urllib.request.OpenerDirector,
    base_url: str,
    user: str,
    password: str,
    job_name: str,
) -> bool:
    url = base_url + f"/job/{urllib.parse.quote(job_name)}/api/json"
    request = build_request(url, user, password)
    try:
        with open_request(opener, request):
            return True
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False
        raise


def parse_params(values: list[str]) -> dict[str, str]:
    params: dict[str, str] = {}
    for item in values:
        key, separator, value = item.partition("=")
        if not separator or not key.strip():
            raise ValueError(f"Expected KEY=VALUE for --param, got {item!r}")
        params[key.strip()] = value
    return params


def fetch_json(
    opener: urllib.request.OpenerDirector,
    url: str,
    user: str,
    password: str,
) -> dict[str, object]:
    request = build_request(url, user, password)
    with open_request(opener, request) as response:
        return json.load(response)


def job_has_parameter_definitions(job_data: dict[str, object]) -> bool:
    actions = job_data.get("actions")
    if not isinstance(actions, list):
        return False
    for action in actions:
        if not isinstance(action, dict):
            continue
        definitions = action.get("parameterDefinitions")
        if isinstance(definitions, list) and definitions:
            return True
    return False


def fetch_console_tail(
    opener: urllib.request.OpenerDirector,
    url: str,
    user: str,
    password: str,
    line_count: int = 120,
) -> str:
    request = build_request(url, user, password)
    with open_request(opener, request) as response:
        payload = response.read().decode("utf-8", errors="replace")
    return "\n".join(payload.splitlines()[-line_count:])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Trigger a Jenkins Pipeline build via buildWithParameters and optionally wait for completion."
    )
    parser.add_argument("--scenario", required=True, choices=sorted(SCENARIOS))
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Optional Jenkins build parameter override. Repeat for multiple values.",
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Trigger the build and exit after Jenkins accepts the queue item.",
    )
    args = parser.parse_args()

    scenario = SCENARIOS[args.scenario]
    env = load_env()
    jenkins_url = validate_local_http_url(
        env.get("JENKINS_URL", "http://localhost:8081/").strip() or "http://localhost:8081/",
        label="Jenkins URL",
        allow_env="LAB_ALLOW_REMOTE_HTTP",
    )
    jenkins_user = env.get("JENKINS_ADMIN_ID", "admin").strip() or "admin"
    jenkins_password = env.get("JENKINS_ADMIN_PASSWORD", "").strip()
    if not jenkins_password:
        raise RuntimeError(
            "JENKINS_ADMIN_PASSWORD is empty. Set it in .env, .env.jenkins, or the current shell."
        )

    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
    )

    if not job_exists(opener, jenkins_url, jenkins_user, jenkins_password, scenario.job_name):
        raise FileNotFoundError(
            f"Jenkins job {scenario.job_name!r} does not exist yet. Run `task jenkins:sync SCENARIO={scenario.scenario}` first."
        )

    user_params = parse_params(args.param)
    params = jenkins_default_params(env, scenario.default_params)
    params.update(user_params)

    print(f"Triggering parameterized Jenkins build for scenario {scenario.scenario}")
    print(f"Jenkins URL: {jenkins_url}")
    print(f"Job name: {scenario.job_name}")
    if params:
        print("Build parameters:")
        for key, value in params.items():
            print(f"  - {key}={value}")
    else:
        print("Build parameters: none (use Jenkinsfile defaults)")

    job_api_url = (
        jenkins_url
        + f"/job/{urllib.parse.quote(scenario.job_name)}/api/json?tree=actions[parameterDefinitions[name]]"
    )
    job_data = fetch_json(opener, job_api_url, jenkins_user, jenkins_password)
    supports_parameters = job_has_parameter_definitions(job_data)
    build_endpoint = "buildWithParameters" if params else "build"
    bootstrap_fallback = False
    data = None
    if params:
        data = urllib.parse.urlencode(params).encode("utf-8")
        if supports_parameters:
            print("Jenkins parameter metadata is visible; using /buildWithParameters.")
        else:
            bootstrap_fallback = True
            print(
                "Jenkins parameter metadata is not visible through the API yet; using /buildWithParameters and retrying /build only if Jenkins rejects the first bootstrap request."
            )
            print(
                "If the fallback is needed, that bootstrap run uses Jenkinsfile defaults; parameter overrides apply on the next accepted buildWithParameters run."
            )

    crumb_headers = fetch_crumb(opener, jenkins_url, jenkins_user, jenkins_password)
    headers = dict(crumb_headers)
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    request = build_request(
        jenkins_url + f"/job/{urllib.parse.quote(scenario.job_name)}/{build_endpoint}",
        jenkins_user,
        jenkins_password,
        method="POST",
        data=data,
        extra_headers=headers,
    )
    try:
        with open_request(opener, request) as response:
            queue_url = response.headers.get("Location", "").strip()
    except urllib.error.HTTPError as exc:
        if not (bootstrap_fallback and exc.code == 400 and build_endpoint == "buildWithParameters"):
            raise
        if user_params or has_install_overrides(params):
            required = ", ".join(sorted(params))
            raise RuntimeError(
                "Jenkins rejected buildWithParameters before parameter metadata was visible, "
                "and this build has required parameter overrides. Refusing to fall back to "
                f"/build because that would drop: {required}. Run `task jenkins:sync "
                f"SCENARIO={scenario.scenario}` again so the lab bootstrap parameters are "
                "seeded, then rerun the build."
            ) from exc
        print(
            "Jenkins rejected buildWithParameters before parameter metadata was visible; retrying the bootstrap controller run via /build."
        )
        request = build_request(
            jenkins_url + f"/job/{urllib.parse.quote(scenario.job_name)}/build",
            jenkins_user,
            jenkins_password,
            method="POST",
            data=None,
            extra_headers=crumb_headers,
        )
        with open_request(opener, request) as response:
            queue_url = response.headers.get("Location", "").strip()

    if not queue_url:
        raise RuntimeError("Jenkins accepted the request but did not return a queue item URL.")

    print(f"Queue item: {queue_url}")
    if args.no_wait:
        print("Exiting without waiting for build completion.")
        return

    queue_api_url = queue_url.rstrip("/") + "/api/json"
    build_url = ""
    previous_queue_message = None
    for _ in range(180):
        queue_data = fetch_json(opener, queue_api_url, jenkins_user, jenkins_password)
        if queue_data.get("cancelled"):
            raise RuntimeError("Jenkins queue item was cancelled before the build started.")
        executable = queue_data.get("executable")
        if isinstance(executable, dict) and executable.get("url"):
            build_url = str(executable["url"]).rstrip("/")
            print(f"Build started: {build_url}")
            break

        queue_message = str(queue_data.get("why") or "waiting")
        if queue_message != previous_queue_message:
            print(f"Queue status: {queue_message}")
            previous_queue_message = queue_message
        time.sleep(2)

    if not build_url:
        raise RuntimeError("Timed out waiting for Jenkins to start the build.")

    build_api_url = build_url + "/api/json"
    build_result = None
    for _ in range(720):
        build_data = fetch_json(opener, build_api_url, jenkins_user, jenkins_password)
        build_number = build_data.get("number")
        building = bool(build_data.get("building"))
        build_result = build_data.get("result")
        print(f"Build #{build_number}: building={building} result={build_result}")
        if not building:
            break
        time.sleep(5)

    console_tail = fetch_console_tail(
        opener,
        build_url + "/consoleText",
        jenkins_user,
        jenkins_password,
    )
    print("--- Console tail ---")
    print(console_tail)

    if build_result != "SUCCESS":
        raise RuntimeError(f"Jenkins build finished with result={build_result}")

    print(f"Build complete: {build_url} result={build_result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - CLI failure path
        print(str(exc), file=sys.stderr)
        sys.exit(1)
