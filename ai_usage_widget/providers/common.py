"""Shared provider utilities."""

from __future__ import annotations

import json
import ssl
import sys
import urllib.error
import urllib.request


class RateLimitError(Exception):
    """Raised when a provider reports rate limiting."""


def fetch_json(provider_name: str, url: str, headers: dict[str, str]) -> dict | None:
    request = urllib.request.Request(url, headers=headers, method="GET")
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, context=context, timeout=15) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise RateLimitError() from exc
        print(
            f"[ai-usage] {provider_name} HTTP {exc.code}: {exc.reason}",
            file=sys.stderr,
        )
        return None
    except Exception as exc:
        print(f"[ai-usage] {provider_name} error: {exc}", file=sys.stderr)
        return None
