"""OpenAI provider helpers."""

from __future__ import annotations

import json
from pathlib import Path

from .. import __version__
from ..constants import OPENAI_API_URL, OPENAI_AUTH_FILE
from ..formatting import format_reset_datetime_unix, format_reset_time_unix
from ..models import ProviderUsage, UsageBucket
from .common import fetch_json


def load_openai_token(
    auth_file: Path = OPENAI_AUTH_FILE,
) -> tuple[str | None, str | None]:
    payload = _read_json(auth_file)
    if not isinstance(payload, dict):
        return None, None
    if payload.get("auth_mode") != "chatgpt":
        return None, None
    tokens = payload.get("tokens", {})
    if not isinstance(tokens, dict):
        return None, None
    return tokens.get("access_token"), tokens.get("account_id")


def fetch_openai_usage(token: str, account_id: str | None) -> dict | None:
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "User-Agent": f"ai-usage-widget/{__version__}",
    }
    if account_id:
        headers["ChatGPT-Account-Id"] = account_id
    return fetch_json("OpenAI", OPENAI_API_URL, headers)


def normalize_openai_usage(data: dict | None) -> ProviderUsage | None:
    if not data:
        return None
    rate_limit = data.get("rate_limit")
    if not isinstance(rate_limit, dict):
        return None

    buckets: dict[str, UsageBucket] = {}
    for input_key, output_key in (
        ("primary_window", "five_hour"),
        ("secondary_window", "seven_day"),
    ):
        window = rate_limit.get(input_key, {}) or {}
        pct = int(window.get("used_percent", 0))
        dec = min(pct / 100, 1.0)
        reset_at = window.get("reset_at")
        buckets[output_key] = UsageBucket(
            pct=pct,
            dec=dec,
            reset_display=format_reset_datetime_unix(reset_at),
            reset_relative=format_reset_time_unix(reset_at),
        )

    return ProviderUsage(
        five_hour=buckets["five_hour"],
        seven_day=buckets["seven_day"],
        plan_type=str(data.get("plan_type", "")),
    )


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload
