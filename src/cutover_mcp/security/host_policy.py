"""Allowlist for the hosts the server sends Cutover API requests to when serving over HTTP.

Over HTTP the API host and instance URL come from request headers or the credentials
form, so callers choose them. Over stdio the server runs on the user's own
machine and its env vars choose them, so nothing here applies.

``TRUSTED_API_HOSTS`` lists the API hosts, comma-separated:

* ``api.cutover.net``: exactly that host.
* ``api.*.cutover.com``: ``*`` matches exactly one label, never ``internal`` or ``corp``.

Every API host is https on the default port. Unset or blank means
:data:`DEFAULT_TRUSTED_API_HOSTS`. The instance URL (``Core-Url``) is checked with the rule
public-api applies to it.
"""

from __future__ import annotations

import ipaddress
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import urlsplit

import httpx

TRUSTED_API_HOSTS_ENV = "TRUSTED_API_HOSTS"
DEFAULT_TRUSTED_API_HOSTS = "api.cutover.net,api.*.cutover.com,api.*.cutover.cloud,api.*.cutover.dev"

# Anything a lenient parser might normalise differently from a strict one.
_FORBIDDEN_CHARS_RE = re.compile(r"[\x00-\x20\x7f\\]")
_LABEL_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")
_HTTPS_PORT = 443
# Labels of zones that never hold an instance or its API.
_INTERNAL_LABELS = frozenset({"internal", "corp"})
_CORE_URL_DOMAINS = frozenset({"cutover.cloud", "cutover.com", "cutover.dev", "cutover.net"})


class UntrustedHostError(ValueError):
    """A URL points somewhere the server must not send requests."""

    def __init__(self, field: str, reason: str):
        self.field = field
        self.reason = reason
        super().__init__(f"{field} is not allowed: {reason}")


@dataclass(frozen=True)
class _HostPattern:
    labels: tuple[str, ...]

    def matches(self, host_labels: tuple[str, ...]) -> bool:
        return len(host_labels) == len(self.labels) and all(
            want == got or (want == "*" and got not in _INTERNAL_LABELS)
            for want, got in zip(self.labels, host_labels, strict=True)
        )


def _is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host.strip("[]"))
        return True
    except ValueError:
        return False


def enforced() -> bool:
    """Whether the allowlist applies: on every transport except stdio, and while serving any HTTP
    request whatever ``MCP_TRANSPORT`` says, e.g. when started with ``fastmcp run --transport http``.
    """
    return os.getenv("MCP_TRANSPORT", "stdio") != "stdio" or _serving_http_request()


def _serving_http_request() -> bool:
    from fastmcp.server.dependencies import get_http_request

    try:
        get_http_request()
    except RuntimeError:
        return False
    return True


@lru_cache(maxsize=8)
def parse_trusted_api_hosts(raw: str) -> frozenset[_HostPattern]:
    """Parse a ``TRUSTED_API_HOSTS`` value.

    A malformed entry raises, so a typo fails the rollout instead of silently trusting
    nothing or something else. A wildcard may not stand in for the last two labels.
    """
    patterns: set[_HostPattern] = set()
    for item in raw.split(","):
        item = item.strip().lower()
        if not item:
            continue
        labels = tuple(item.split("."))
        if (
            len(labels) < 2
            or _is_ip(item)
            or "*" in labels[-2:]
            or not all(label == "*" or _LABEL_RE.match(label) for label in labels)
        ):
            raise ValueError(f"invalid {TRUSTED_API_HOSTS_ENV} entry: {item!r}")
        patterns.add(_HostPattern(labels))
    if not patterns:
        raise ValueError(f"{TRUSTED_API_HOSTS_ENV} lists no hosts")
    return frozenset(patterns)


def trusted_api_hosts() -> frozenset[_HostPattern]:
    """The configured ``TRUSTED_API_HOSTS``, or the default when unset or blank."""
    raw = os.getenv(TRUSTED_API_HOSTS_ENV, "")
    return parse_trusted_api_hosts(raw if raw.strip() else DEFAULT_TRUSTED_API_HOSTS)


def _https_host(url: object, field: str) -> str:
    """The lower-cased host of ``url`` once it is https on the default port, with no userinfo,
    query or fragment, and names the same host httpx will connect to.

    Paths are appended to these URLs, and a query or fragment would swallow the appended path.
    """
    if not isinstance(url, str) or not url:
        raise UntrustedHostError(field, "it is not a URL")
    if _FORBIDDEN_CHARS_RE.search(url) or not url.isascii():
        raise UntrustedHostError(field, "it contains whitespace, control, backslash or non-ASCII characters")
    try:
        parts = urlsplit(url)
        port = parts.port
        sent = httpx.URL(url)
    except (ValueError, httpx.InvalidURL) as exc:
        raise UntrustedHostError(field, "it is not a valid URL") from exc

    host = (parts.hostname or "").lower()
    if parts.scheme.lower() != "https":
        raise UntrustedHostError(field, "only https URLs are allowed")
    if "@" in parts.netloc:
        raise UntrustedHostError(field, "userinfo is not allowed")
    if parts.fragment or "#" in url:
        raise UntrustedHostError(field, "a fragment is not allowed")
    if parts.query or "?" in url:
        raise UntrustedHostError(field, "a query string is not allowed")
    if port not in (None, _HTTPS_PORT):
        raise UntrustedHostError(field, "only the default https port is allowed")
    if not host or sent.host.lower() != host or (sent.port or _HTTPS_PORT) != (port or _HTTPS_PORT):
        raise UntrustedHostError(field, "the host is ambiguous")
    if _is_ip(host):
        raise UntrustedHostError(field, "IP addresses are not allowed")
    if not all(_LABEL_RE.match(label) for label in host.split(".")):
        raise UntrustedHostError(field, "the host is malformed")
    return host


def check_api_url(url: object, trusted: frozenset[_HostPattern], *, field: str) -> str:
    """Return ``url`` if it targets a trusted API host, else raise :class:`UntrustedHostError`."""
    host = _https_host(url, field)
    if any(pattern.matches(tuple(host.split("."))) for pattern in trusted):
        return url
    raise UntrustedHostError(field, f"{host!r} is not a trusted Cutover API host")


def check_core_url(url: object, *, field: str = "Core-Url") -> str:
    """Return ``url`` if it is a Cutover instance URL, else raise :class:`UntrustedHostError`.

    The first label is the instance name, so a tenant called e.g. ``corp`` is allowed.
    """
    host = _https_host(url, field)
    labels = host.split(".")
    if ".".join(labels[-2:]) in _CORE_URL_DOMAINS and not _INTERNAL_LABELS.intersection(labels[1:]):
        return url
    raise UntrustedHostError(field, f"{host!r} is not a Cutover instance host")
