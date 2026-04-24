from __future__ import annotations

from dataclasses import dataclass
from http import client
import os
from urllib.parse import urlparse, urlsplit

LOCAL_HTTP_HOSTS = {
    "localhost",
    "127.0.0.1",
    "::1",
    "host.docker.internal",
}


def _is_truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def validate_local_http_url(raw_url: str, *, label: str, allow_env: str | None = None) -> str:
    """Return a normalized local lab URL or raise with a user-actionable message."""
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{label} must be an http(s) URL, got {raw_url!r}.")

    host = (parsed.hostname or "").lower()
    insecure_override = _is_truthy(os.getenv(allow_env)) if allow_env else False
    if parsed.scheme == "http" and host not in LOCAL_HTTP_HOSTS and not insecure_override:
        override = f" Set {allow_env}=true to allow it intentionally." if allow_env else ""
        raise ValueError(
            f"{label} uses plain HTTP to non-local host {host!r}. "
            f"Use https:// for remote targets or a localhost URL for this lab.{override}"
        )

    return raw_url.rstrip("/")


@dataclass(frozen=True)
class SafeHttpResponse:
    status: int
    body: str
    headers: dict[str, str]


def safe_http_get(
    raw_url: str,
    *,
    label: str,
    headers: dict[str, str] | None = None,
    timeout: float = 5.0,
    allow_env: str | None = None,
) -> SafeHttpResponse:
    """GET a validated lab URL without accepting non-HTTP schemes."""
    url = validate_local_http_url(raw_url, label=label, allow_env=allow_env)
    parsed = urlsplit(url)
    host = parsed.hostname
    if not host:
        raise ValueError(f"{label} must include a hostname, got {raw_url!r}.")

    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"

    connection_cls = client.HTTPSConnection if parsed.scheme == "https" else client.HTTPConnection
    connection = connection_cls(host, port=parsed.port, timeout=timeout)
    try:
        connection.request("GET", path, headers=headers or {})
        response = connection.getresponse()
        body = response.read().decode("utf-8", "ignore")
        return SafeHttpResponse(
            status=response.status,
            body=body,
            headers={key: value for key, value in response.getheaders()},
        )
    finally:
        connection.close()
