"""Claude provider helpers."""

from __future__ import annotations

import json
from pathlib import Path

from .. import __version__
from ..constants import CLAUDE_API_URL, CLAUDE_CREDENTIALS, CONFIG_FILE
from ..formatting import format_reset_datetime, format_reset_time
from ..models import ClaudeSubscriptionInfo, ProviderUsage, UsageBucket
from .common import fetch_json


def load_claude_token(
    credentials_file: Path = CLAUDE_CREDENTIALS,
    config_file: Path = CONFIG_FILE,
) -> str | None:
    data = _read_json(credentials_file)
    if isinstance(data, dict):
        token = data.get("claudeAiOauth", {}).get("accessToken")
        if token:
            return token

    data = _read_json(config_file)
    if isinstance(data, dict):
        token = data.get("oauth_token")
        if token:
            return token
    return None


def load_claude_subscription_info(
    credentials_file: Path = CLAUDE_CREDENTIALS,
) -> ClaudeSubscriptionInfo | None:
    data = _read_json(credentials_file)
    if not isinstance(data, dict):
        return None
    oauth = data.get("claudeAiOauth", {})
    if not oauth:
        return None
    return ClaudeSubscriptionInfo(
        subscription_type=str(oauth.get("subscriptionType", "")).title(),
        rate_limit_tier=str(oauth.get("rateLimitTier", "")),
    )


def save_claude_token(token: str, config_file: Path = CONFIG_FILE) -> None:
    config_file.parent.mkdir(parents=True, exist_ok=True)
    payload = _read_json(config_file)
    if not isinstance(payload, dict):
        payload = {}
    payload["oauth_token"] = token
    config_file.write_text(json.dumps(payload, indent=2) + "\n")
    config_file.chmod(0o600)


def fetch_claude_usage(token: str) -> dict | None:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": f"ai-usage-widget/{__version__}",
        "Authorization": f"Bearer {token}",
        "anthropic-beta": "oauth-2025-04-20",
    }
    return fetch_json("Claude", CLAUDE_API_URL, headers)


def normalize_claude_usage(data: dict | None) -> ProviderUsage | None:
    if not data:
        return None

    buckets: dict[str, UsageBucket] = {}
    for input_key, output_key in (
        ("five_hour", "five_hour"),
        ("seven_day", "seven_day"),
    ):
        bucket = data.get(input_key, {}) or {}
        utilization = bucket.get("utilization", 0)
        if utilization >= 1:
            pct = int(utilization)
            dec = min(utilization / 100, 1.0)
        else:
            pct = int(utilization * 100)
            dec = utilization
        reset_at = bucket.get("resets_at")
        buckets[output_key] = UsageBucket(
            pct=pct,
            dec=dec,
            reset_display=format_reset_datetime(reset_at),
            reset_relative=format_reset_time(reset_at),
        )

    return ProviderUsage(
        five_hour=buckets["five_hour"],
        seven_day=buckets["seven_day"],
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
