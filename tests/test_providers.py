import json

from ai_usage_widget.providers.claude import (
    load_claude_subscription_info,
    load_claude_token,
    normalize_claude_usage,
    save_claude_token,
)
from ai_usage_widget.providers.openai import load_openai_token, normalize_openai_usage


def test_load_claude_token_prefers_cli_credentials(tmp_path):
    credentials_file = tmp_path / "credentials.json"
    config_file = tmp_path / "config.json"
    credentials_file.write_text(
        json.dumps({"claudeAiOauth": {"accessToken": "cred-token"}})
    )
    config_file.write_text(json.dumps({"oauth_token": "config-token"}))

    token = load_claude_token(
        credentials_file=credentials_file,
        config_file=config_file,
    )

    assert token == "cred-token"


def test_save_claude_token_preserves_existing_config(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"providers": ["claude"]}))

    save_claude_token("saved-token", config_file=config_file)

    payload = json.loads(config_file.read_text())
    assert payload["providers"] == ["claude"]
    assert payload["oauth_token"] == "saved-token"


def test_load_claude_subscription_info_reads_metadata(tmp_path):
    credentials_file = tmp_path / "credentials.json"
    credentials_file.write_text(
        json.dumps(
            {
                "claudeAiOauth": {
                    "subscriptionType": "pro",
                    "rateLimitTier": "tier-1",
                }
            }
        )
    )

    info = load_claude_subscription_info(credentials_file)

    assert info is not None
    assert info.subscription_type == "Pro"
    assert info.rate_limit_tier == "tier-1"


def test_normalize_claude_usage_handles_fractional_utilization():
    usage = normalize_claude_usage(
        {
            "five_hour": {"utilization": 0.42, "resets_at": "2099-01-01T12:00:00Z"},
            "seven_day": {"utilization": 88, "resets_at": "2099-01-03T12:00:00Z"},
        }
    )

    assert usage is not None
    assert usage.five_hour.pct == 42
    assert usage.five_hour.dec == 0.42
    assert usage.seven_day.pct == 88
    assert usage.seven_day.dec == 0.88


def test_load_openai_token_requires_chatgpt_mode(tmp_path):
    auth_file = tmp_path / "auth.json"
    auth_file.write_text(
        json.dumps(
            {
                "auth_mode": "chatgpt",
                "tokens": {
                    "access_token": "openai-token",
                    "account_id": "acct-123",
                },
            }
        )
    )

    token, account_id = load_openai_token(auth_file=auth_file)

    assert token == "openai-token"
    assert account_id == "acct-123"


def test_normalize_openai_usage_reads_plan_and_windows():
    usage = normalize_openai_usage(
        {
            "plan_type": "plus",
            "rate_limit": {
                "primary_window": {"used_percent": 8, "reset_at": 4102444800},
                "secondary_window": {"used_percent": 3, "reset_at": 4102531200},
            },
        }
    )

    assert usage is not None
    assert usage.plan_type == "plus"
    assert usage.five_hour.pct == 8
    assert usage.seven_day.pct == 3
