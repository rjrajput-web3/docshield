"""Thin client for the Clocked API (https://clocked.rezolve.ai/clocked).

Design notes:
- The API key is read from the CLOCKED_API_KEY environment variable and is
  only ever used server-side. It is never logged and never sent to browsers.
- Every logical request gets one Idempotency-Key (UUID). Retries of the same
  logical request reuse the same key, so Clocked will not double-charge.
- Timeouts are bounded but generous: model calls can take a while, so the
  read timeout is 150 s (connect 15 s) instead of a short default.
- Billing is in model-time credits; the actual debit for each call comes
  back in the X-Clocked-Credits response header and is surfaced to callers.
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass

import httpx

DEFAULT_BASE_URL = "https://clocked.rezolve.ai/clocked"

_TIMEOUT = httpx.Timeout(connect=15.0, read=150.0, write=30.0, pool=15.0)
_MAX_ATTEMPTS = 2  # one retry on transport errors / 5xx, same idempotency key


class ClockedError(Exception):
    """Raised when the Clocked API returns an error or cannot be reached."""

    def __init__(self, message: str, status: int | None = None, body: str = ""):
        super().__init__(message)
        self.status = status
        self.body = body


@dataclass
class ClockedResult:
    data: dict
    credits: str | None  # X-Clocked-Credits header (model-time credits debited)
    cost_usd: str | None  # X-Clocked-Cost-Usd header, when present
    elapsed_s: float


def _client() -> httpx.Client:
    """Build an HTTP client that works on plain hosts (e.g. Vercel) and
    behind a TLS-intercepting egress proxy (some dev VMs): when the standard
    HTTPS_PROXY / SSL_CERT_FILE environment variables are present, honour
    them explicitly. trust_env=False also avoids httpx misparsing bracketed
    IPv6 entries in NO_PROXY on some systems."""
    proxy = (
        os.environ.get("CLOCKED_PROXY")
        or os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
        or None
    )
    verify = os.environ.get("SSL_CERT_FILE") or True
    return httpx.Client(timeout=_TIMEOUT, proxy=proxy, trust_env=False, verify=verify)


def _api_key() -> str:
    key = os.environ.get("CLOCKED_API_KEY", "").strip()
    if not key:
        raise ClockedError(
            "CLOCKED_API_KEY is not configured on the server.", status=None
        )
    return key


def _base_url() -> str:
    return os.environ.get("CLOCKED_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def post(path: str, payload: dict) -> ClockedResult:
    """POST one logical request to a Clocked endpoint (e.g. '/pii')."""
    url = f"{_base_url()}{path}"
    headers = {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
        "Idempotency-Key": str(uuid.uuid4()),
    }
    last_error: Exception | None = None
    started = time.monotonic()
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            with _client() as client:
                resp = client.post(url, json=payload, headers=headers)
            elapsed = time.monotonic() - started
            if resp.status_code >= 500 and attempt < _MAX_ATTEMPTS:
                continue  # retry with the same idempotency key
            if resp.status_code >= 400:
                raise ClockedError(
                    f"Clocked API error (HTTP {resp.status_code})",
                    status=resp.status_code,
                    body=resp.text[:800],
                )
            return ClockedResult(
                data=resp.json(),
                credits=resp.headers.get("x-clocked-credits"),
                cost_usd=resp.headers.get("x-clocked-cost-usd"),
                elapsed_s=elapsed,
            )
        except httpx.HTTPError as exc:  # transport error / timeout
            last_error = exc
            if attempt < _MAX_ATTEMPTS:
                continue
    raise ClockedError(
        f"Clocked API request to {path} failed after {_MAX_ATTEMPTS} attempts: "
        f"{type(last_error).__name__ if last_error else 'unknown error'}"
    )
