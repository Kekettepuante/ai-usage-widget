"""Configuration loading and validation."""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .constants import CONFIG_FILE, VALID_POSITIONS, VALID_PROVIDERS

HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


@dataclass(frozen=True, slots=True)
class AppConfig:
    providers: tuple[str, ...] = ("claude", "openai")
    position: str = "top-right"
    margin_x: int = 10
    margin_y: int = 4
    font_family: str = "Sans"
    font_size: int = 11
    color_claude: str = "#D97757"
    color_openai: str = "#10A37F"
    color_low: str = "#22c55e"
    color_medium: str = "#eab308"
    color_high: str = "#f97316"
    color_critical: str = "#ef4444"
    threshold_medium: int = 50
    threshold_high: int = 75
    threshold_critical: int = 90
    refresh_interval: int = 120
    notifications: bool = True

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "providers": list(self.providers),
            "position": self.position,
            "margin_x": self.margin_x,
            "margin_y": self.margin_y,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "color_claude": self.color_claude,
            "color_openai": self.color_openai,
            "color_low": self.color_low,
            "color_medium": self.color_medium,
            "color_high": self.color_high,
            "color_critical": self.color_critical,
            "threshold_medium": self.threshold_medium,
            "threshold_high": self.threshold_high,
            "threshold_critical": self.threshold_critical,
            "refresh_interval": self.refresh_interval,
            "notifications": self.notifications,
        }

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> tuple[AppConfig, list[str]]:
        warnings: list[str] = []
        defaults = cls()

        providers = _coerce_providers(
            raw.get("providers"),
            defaults.providers,
            warnings,
        )
        position = _coerce_choice(
            raw.get("position"),
            defaults.position,
            set(VALID_POSITIONS),
            "position",
            warnings,
        )
        margin_x = _coerce_int(
            raw.get("margin_x"),
            defaults.margin_x,
            "margin_x",
            warnings,
            0,
            1000,
        )
        margin_y = _coerce_int(
            raw.get("margin_y"),
            defaults.margin_y,
            "margin_y",
            warnings,
            0,
            1000,
        )
        font_family = _coerce_text(
            raw.get("font_family"),
            defaults.font_family,
            "font_family",
            warnings,
        )
        font_size = _coerce_int(
            raw.get("font_size"),
            defaults.font_size,
            "font_size",
            warnings,
            6,
            72,
        )

        color_claude = _coerce_color(
            raw.get("color_claude"),
            defaults.color_claude,
            "color_claude",
            warnings,
        )
        color_openai = _coerce_color(
            raw.get("color_openai"),
            defaults.color_openai,
            "color_openai",
            warnings,
        )
        color_low = _coerce_color(
            raw.get("color_low"),
            defaults.color_low,
            "color_low",
            warnings,
        )
        color_medium = _coerce_color(
            raw.get("color_medium"),
            defaults.color_medium,
            "color_medium",
            warnings,
        )
        color_high = _coerce_color(
            raw.get("color_high"),
            defaults.color_high,
            "color_high",
            warnings,
        )
        color_critical = _coerce_color(
            raw.get("color_critical"),
            defaults.color_critical,
            "color_critical",
            warnings,
        )

        threshold_medium = _coerce_int(
            raw.get("threshold_medium"),
            defaults.threshold_medium,
            "threshold_medium",
            warnings,
            0,
            100,
        )
        threshold_high = _coerce_int(
            raw.get("threshold_high"),
            defaults.threshold_high,
            "threshold_high",
            warnings,
            0,
            100,
        )
        threshold_critical = _coerce_int(
            raw.get("threshold_critical"),
            defaults.threshold_critical,
            "threshold_critical",
            warnings,
            0,
            100,
        )
        if not (threshold_medium < threshold_high < threshold_critical):
            warnings.append(
                "threshold ordering must satisfy threshold_medium < "
                "threshold_high < threshold_critical; using defaults"
            )
            threshold_medium = defaults.threshold_medium
            threshold_high = defaults.threshold_high
            threshold_critical = defaults.threshold_critical

        refresh_interval = _coerce_int(
            raw.get("refresh_interval"),
            defaults.refresh_interval,
            "refresh_interval",
            warnings,
            10,
            3600,
        )
        notifications = _coerce_bool(
            raw.get("notifications"),
            defaults.notifications,
            "notifications",
            warnings,
        )

        return (
            cls(
                providers=providers,
                position=position,
                margin_x=margin_x,
                margin_y=margin_y,
                font_family=font_family,
                font_size=font_size,
                color_claude=color_claude,
                color_openai=color_openai,
                color_low=color_low,
                color_medium=color_medium,
                color_high=color_high,
                color_critical=color_critical,
                threshold_medium=threshold_medium,
                threshold_high=threshold_high,
                threshold_critical=threshold_critical,
                refresh_interval=refresh_interval,
                notifications=notifications,
            ),
            warnings,
        )


def load_config(config_file: Path = CONFIG_FILE) -> AppConfig:
    raw = read_raw_config(config_file)
    if raw is None:
        config = AppConfig()
        write_default_config(config_file, config)
        return config

    config, warnings = AppConfig.from_mapping(raw)
    for warning in warnings:
        print(f"[ai-usage] Invalid config: {warning}", file=sys.stderr)
    return config


def read_raw_config(config_file: Path = CONFIG_FILE) -> dict[str, Any] | None:
    if not config_file.exists():
        return None
    try:
        payload = json.loads(config_file.read_text())
    except json.JSONDecodeError as exc:
        print(
            f"[ai-usage] Invalid config.json ({exc}); using defaults",
            file=sys.stderr,
        )
        return {}
    if not isinstance(payload, dict):
        print(
            "[ai-usage] config.json must contain a JSON object; using defaults",
            file=sys.stderr,
        )
        return {}
    return payload


def write_default_config(config_file: Path, config: AppConfig) -> None:
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(json.dumps(config.to_json_dict(), indent=2) + "\n")
    config_file.chmod(0o600)


def _coerce_providers(
    value: Any,
    default: tuple[str, ...],
    warnings: list[str],
) -> tuple[str, ...]:
    if value is None:
        return default
    if not isinstance(value, list):
        warnings.append("providers must be a list; using defaults")
        return default
    providers: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str) or item not in VALID_PROVIDERS:
            warnings.append(f"unsupported provider {item!r}; ignoring")
            continue
        if item not in seen:
            providers.append(item)
            seen.add(item)
    if not providers:
        warnings.append("providers list is empty after validation; using defaults")
        return default
    return tuple(providers)


def _coerce_choice(
    value: Any,
    default: str,
    valid: set[str],
    field_name: str,
    warnings: list[str],
) -> str:
    if value is None:
        return default
    if not isinstance(value, str) or value not in valid:
        warnings.append(f"{field_name} must be one of {sorted(valid)}; using default")
        return default
    return value


def _coerce_text(
    value: Any,
    default: str,
    field_name: str,
    warnings: list[str],
) -> str:
    if value is None:
        return default
    if not isinstance(value, str) or not value.strip():
        warnings.append(f"{field_name} must be a non-empty string; using default")
        return default
    return value.strip()


def _coerce_color(
    value: Any,
    default: str,
    field_name: str,
    warnings: list[str],
) -> str:
    if value is None:
        return default
    if not isinstance(value, str) or not HEX_COLOR_RE.fullmatch(value):
        warnings.append(f"{field_name} must be a hex color; using default")
        return default
    return value


def _coerce_int(
    value: Any,
    default: int,
    field_name: str,
    warnings: list[str],
    lower: int,
    upper: int,
) -> int:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        warnings.append(f"{field_name} must be an integer; using default")
        return default
    if not (lower <= value <= upper):
        warnings.append(
            f"{field_name} must be between {lower} and {upper}; using default"
        )
        return default
    return value


def _coerce_bool(
    value: Any,
    default: bool,
    field_name: str,
    warnings: list[str],
) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        warnings.append(f"{field_name} must be a boolean; using default")
        return default
    return value
