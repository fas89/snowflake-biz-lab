from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from http.cookiejar import CookieJar
from pathlib import Path
from urllib import error, parse, request

from local_env_utils import parse_env_file, update_env_file


@dataclass
class BootstrapConfig:
    web_base_url: str
    mailhog_base_url: str
    admin_email: str
    admin_password: str
    organization_name: str
    organization_vanity_url: str
    api_key_name: str
    timeout_seconds: int
    poll_interval_seconds: float


def read_env_with_fallback(primary: Path, fallback: Path) -> dict[str, str]:
    values = parse_env_file(fallback)
    for key, value in parse_env_file(primary).items():
        if value:
            values[key] = value
    return values


def build_opener() -> request.OpenerDirector:
    return request.build_opener(request.HTTPCookieProcessor(CookieJar()))


def http_request(
    opener: request.OpenerDirector,
    url: str,
    *,
    method: str = "GET",
    data: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, str, dict[str, str], str]:
    encoded = None
    merged_headers = dict(headers or {})
    if data is not None:
        encoded = parse.urlencode(data).encode("utf-8")
        merged_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

    req = request.Request(url, data=encoded, headers=merged_headers, method=method)
    try:
        with opener.open(req) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8", "ignore")
            final_url = resp.geturl()
            return status, body, dict(resp.headers.items()), final_url
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", "ignore")
        return exc.code, body, dict(exc.headers.items()), exc.geturl()


def wait_for_ready(url: str, timeout_seconds: int, poll_interval_seconds: float) -> None:
    deadline = time.time() + timeout_seconds
    opener = build_opener()
    while time.time() < deadline:
        try:
            status, _, _, _ = http_request(opener, url)
            if status == 200:
                return
        except (error.URLError, OSError):
            pass
        time.sleep(poll_interval_seconds)
    raise RuntimeError(f"Timed out waiting for {url}")


def extract_hidden_value(html: str, field_name: str) -> str:
    match = re.search(
        rf'name="{re.escape(field_name)}"\s+value="([^"]+)"',
        html,
        flags=re.IGNORECASE,
    )
    if not match:
        raise RuntimeError(f"Could not find hidden field '{field_name}'")
    return match.group(1)


def extract_meta_value(html: str, meta_name: str) -> str:
    match = re.search(
        rf'<meta name="{re.escape(meta_name)}" content="([^"]+)"',
        html,
        flags=re.IGNORECASE,
    )
    if not match:
        raise RuntimeError(f"Could not find meta value '{meta_name}'")
    return match.group(1)


def fetch_mailhog_messages(mailhog_base_url: str) -> list[dict]:
    with request.urlopen(f"{mailhog_base_url}/api/v2/messages") as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload.get("items", [])


def find_verification_link(
    mailhog_base_url: str,
    email: str,
    *,
    existing_ids: set[str],
    timeout_seconds: int,
    poll_interval_seconds: float,
) -> str:
    mailbox, _, domain = email.partition("@")
    deadline = time.time() + timeout_seconds
    pattern = re.compile(r"(https?://[^\s]+/verify\?token=[A-Za-z0-9]+)")

    while time.time() < deadline:
        for message in fetch_mailhog_messages(mailhog_base_url):
            message_id = message.get("ID")
            if message_id in existing_ids:
                continue

            recipients = message.get("To", [])
            if not any(
                recipient.get("Mailbox") == mailbox and recipient.get("Domain") == domain
                for recipient in recipients
            ):
                continue

            body = message.get("Content", {}).get("Body", "")
            match = pattern.search(body)
            if match:
                return match.group(1)

        time.sleep(poll_interval_seconds)

    raise RuntimeError("Timed out waiting for the Entropy verification email in MailHog")


def is_logged_in(opener: request.OpenerDirector, web_base_url: str) -> bool:
    status, body, _, _ = http_request(opener, f"{web_base_url}/organizations")
    return status == 200 and "Your Organizations" in body


def is_superadmin(opener: request.OpenerDirector, web_base_url: str) -> bool:
    status, body, _, _ = http_request(opener, f"{web_base_url}/admin")
    return status == 200 and "/admin/organizations" in body


def login(opener: request.OpenerDirector, web_base_url: str, email: str, password: str) -> bool:
    status, body, _, _ = http_request(opener, f"{web_base_url}/login")
    if status != 200:
        raise RuntimeError(f"Could not load login page at {web_base_url}/login")

    csrf = extract_hidden_value(body, "_csrf")
    http_request(
        opener,
        f"{web_base_url}/login",
        method="POST",
        data={"_csrf": csrf, "username": email, "password": password},
    )
    return is_logged_in(opener, web_base_url)


def create_account(opener: request.OpenerDirector, config: BootstrapConfig) -> None:
    status, body, _, _ = http_request(opener, f"{config.web_base_url}/create-account")
    if status != 200:
        raise RuntimeError("Could not load the Entropy create-account page")

    csrf = extract_hidden_value(body, "_csrf")
    existing_ids = {message.get("ID", "") for message in fetch_mailhog_messages(config.mailhog_base_url)}

    status, body, _, _ = http_request(
        opener,
        f"{config.web_base_url}/create-account",
        method="POST",
        data={
            "_csrf": csrf,
            "ref": "",
            "fullName": "Local Demo Admin",
            "email": config.admin_email,
            "password": config.admin_password,
            "termsAccepted": "v1",
            "_termsAccepted": "on",
        },
    )
    if status not in {200, 302}:
        raise RuntimeError("Entropy account creation failed unexpectedly")

    verify_link = find_verification_link(
        config.mailhog_base_url,
        config.admin_email,
        existing_ids=existing_ids,
        timeout_seconds=config.timeout_seconds,
        poll_interval_seconds=config.poll_interval_seconds,
    )
    verify_status, _, _, _ = http_request(opener, verify_link)
    if verify_status != 200:
        raise RuntimeError("Entropy email verification failed")


def organization_api_keys_path(config: BootstrapConfig) -> str:
    return f"{config.web_base_url}/{config.organization_vanity_url}/settings/api-keys"


def ensure_organization(opener: request.OpenerDirector, config: BootstrapConfig) -> None:
    status, _, _, _ = http_request(opener, organization_api_keys_path(config))
    if status == 200:
        return

    status, body, _, _ = http_request(opener, f"{config.web_base_url}/welcome")
    if status != 200:
        raise RuntimeError("Could not load the Entropy welcome page to create the organization")

    csrf = extract_meta_value(body, "_csrf")
    csrf_header = extract_meta_value(body, "_csrf_header")

    create_status, _, headers, _ = http_request(
        opener,
        f"{config.web_base_url}/organizations/save",
        method="POST",
        data={
            "fullName": config.organization_name,
            "host": config.web_base_url,
            "vanityUrl": config.organization_vanity_url,
        },
        headers={csrf_header: csrf},
    )
    if create_status not in {200, 302}:
        raise RuntimeError("Entropy organization creation failed")

    status, _, _, _ = http_request(opener, organization_api_keys_path(config))
    if status != 200:
        raise RuntimeError(
            f"Entropy organization '{config.organization_vanity_url}' was not reachable after creation"
        )


def create_api_key(opener: request.OpenerDirector, config: BootstrapConfig) -> str:
    add_path = f"{organization_api_keys_path(config)}/add"
    status, body, _, _ = http_request(opener, add_path)
    if status != 200:
        raise RuntimeError("Could not load the Entropy add API key page")

    csrf = extract_hidden_value(body, "_csrf")
    status, body, _, _ = http_request(
        opener,
        f"{config.web_base_url}/{config.organization_vanity_url}/settings/api-keys/save",
        method="POST",
        data={
            "_csrf": csrf,
            "displayName": config.api_key_name,
            "scope": "organization",
        },
    )
    if status != 200:
        raise RuntimeError("Entropy API key creation failed")

    match = re.search(r'(ed_live_[A-Za-z0-9_]+)', body)
    if not match:
        raise RuntimeError("Could not extract the generated Entropy API key")
    return match.group(1)


def validate_api_key(web_base_url: str, api_key: str) -> bool:
    opener = build_opener()
    status, _, _, _ = http_request(
        opener,
        f"{web_base_url}/api/teams",
        headers={"x-api-key": api_key},
    )
    return status == 200


def bootstrap_entropy(config: BootstrapConfig) -> str:
    opener = build_opener()
    if not login(opener, config.web_base_url, config.admin_email, config.admin_password):
        create_account(opener, config)
        if not login(opener, config.web_base_url, config.admin_email, config.admin_password):
            raise RuntimeError("Entropy login failed after account creation")

    if not is_superadmin(opener, config.web_base_url):
        raise RuntimeError(
            f"The configured bootstrap user '{config.admin_email}' is not a superadmin in Entropy"
        )

    ensure_organization(opener, config)
    return create_api_key(opener, config)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bootstrap the local Entropy CE signup flow and generate a reusable DMM API key."
    )
    parser.add_argument(
        "--catalog-env-file",
        default=".env.catalogs",
        help="Path to the local catalog environment file. Defaults to .env.catalogs.",
    )
    parser.add_argument(
        "--fluid-secrets-file",
        default="runtime/generated/fluid.local.env",
        help="Path to the ignored FLUID secrets file that should receive DMM_API_URL and DMM_API_KEY.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=120,
        help="How long to wait for Entropy or MailHog to become ready.",
    )
    parser.add_argument(
        "--poll-interval-seconds",
        type=float,
        default=2.0,
        help="Polling interval while waiting for local services.",
    )
    args = parser.parse_args()

    catalog_env_file = Path(args.catalog_env_file).expanduser().resolve()
    catalog_env = read_env_with_fallback(
        catalog_env_file,
        catalog_env_file.with_name(f"{catalog_env_file.name}.example"),
    )
    fluid_secrets_file = Path(args.fluid_secrets_file).expanduser().resolve()
    fluid_secrets = parse_env_file(fluid_secrets_file)

    web_base_url = (
        catalog_env.get("ENTROPY_EXTERNAL_URL")
        or catalog_env.get("DMM_API_URL")
        or "http://localhost:8095"
    ).rstrip("/")
    mailhog_base_url = f"http://localhost:{catalog_env.get('MAILHOG_UI_PORT', '8026')}"

    config = BootstrapConfig(
        web_base_url=web_base_url,
        mailhog_base_url=mailhog_base_url,
        admin_email=(
            catalog_env.get("ENTROPY_BOOTSTRAP_ADMIN_EMAIL")
            or catalog_env.get("ENTROPY_SUPERADMINS", "admin@example.com").split(",")[0].strip()
        ),
        admin_password=catalog_env.get("ENTROPY_BOOTSTRAP_ADMIN_PASSWORD", "change_me"),
        organization_name=catalog_env.get("ENTROPY_BOOTSTRAP_ORG_NAME", "Telco Demo Org"),
        organization_vanity_url=catalog_env.get("ENTROPY_BOOTSTRAP_ORG_VANITY_URL", "telcodemo"),
        api_key_name=catalog_env.get("ENTROPY_BOOTSTRAP_API_KEY_NAME", "Local DMM Key"),
        timeout_seconds=args.timeout_seconds,
        poll_interval_seconds=args.poll_interval_seconds,
    )

    update_env_file(
        catalog_env_file,
        {
            "ENTROPY_BOOTSTRAP_ADMIN_EMAIL": config.admin_email,
            "ENTROPY_BOOTSTRAP_ADMIN_PASSWORD": config.admin_password,
            "ENTROPY_BOOTSTRAP_ORG_NAME": config.organization_name,
            "ENTROPY_BOOTSTRAP_ORG_VANITY_URL": config.organization_vanity_url,
            "ENTROPY_BOOTSTRAP_API_KEY_NAME": config.api_key_name,
        },
    )

    wait_for_ready(f"{config.web_base_url}/actuator/health", config.timeout_seconds, config.poll_interval_seconds)
    wait_for_ready(f"{config.mailhog_base_url}/api/v2/messages", config.timeout_seconds, config.poll_interval_seconds)

    existing_api_key = fluid_secrets.get("DMM_API_KEY", "")
    if existing_api_key and validate_api_key(config.web_base_url, existing_api_key):
        update_env_file(
            fluid_secrets_file,
            {
                "DMM_API_URL": config.web_base_url,
                "DMM_API_KEY": existing_api_key,
            },
        )
        print("Existing local DMM_API_KEY is already valid.")
        print(f"DMM_API_URL={config.web_base_url}")
        return

    api_key = bootstrap_entropy(config)
    if not validate_api_key(config.web_base_url, api_key):
        raise RuntimeError("The generated Entropy API key did not validate against /api/teams")

    update_env_file(
        fluid_secrets_file,
        {
            "DMM_API_URL": config.web_base_url,
            "DMM_API_KEY": api_key,
        },
    )
    print("Local Entropy bootstrap complete.")
    print(f"Admin email: {config.admin_email}")
    print(f"Organization vanity URL: {config.organization_vanity_url}")
    print(f"DMM_API_URL={config.web_base_url}")
    print(f"Updated {fluid_secrets_file} with a fresh DMM_API_KEY")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Entropy bootstrap failed: {exc}", file=sys.stderr)
        sys.exit(1)
