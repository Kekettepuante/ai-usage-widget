"""Pure presentation helpers for overlay rendering."""

from __future__ import annotations

from .config import AppConfig
from .formatting import escape_markup_attr, escape_markup_text
from .models import OverlayDisplayData, ProviderUsage

COLOR_GRAY = "#888888"


def get_color_for_pct(dec: float, config: AppConfig) -> str:
    if dec < config.threshold_medium / 100:
        return config.color_low
    if dec < config.threshold_high / 100:
        return config.color_medium
    if dec < config.threshold_critical / 100:
        return config.color_high
    return config.color_critical


def overlay_display_from_usage(
    usage: ProviderUsage | None,
    config: AppConfig,
) -> OverlayDisplayData | None:
    if usage is None:
        return None
    return OverlayDisplayData(
        pct5=f"{usage.five_hour.pct}%",
        pct7=f"{usage.seven_day.pct}%",
        c5=get_color_for_pct(usage.five_hour.dec, config),
        c7=get_color_for_pct(usage.seven_day.dec, config),
        r5=usage.five_hour.reset_display,
        r7=usage.seven_day.reset_display,
    )


def overlay_error_display() -> OverlayDisplayData:
    return OverlayDisplayData(
        pct5="ERR",
        pct7="ERR",
        c5=COLOR_GRAY,
        c7=COLOR_GRAY,
    )


def build_provider_line(
    icon: str,
    icon_color: str,
    data: OverlayDisplayData | None,
    config: AppConfig,
) -> str:
    font_family = escape_markup_attr(config.font_family)
    font_size = config.font_size
    label_size = font_size - 1
    reset_size = font_size - 3
    spacer_size = font_size - 2

    prefix = (
        f'<span color="{escape_markup_attr(icon_color)}" '
        f'font_desc="{font_family} Bold {font_size}">'
        f"{escape_markup_text(icon)} </span>"
    )
    if data is None:
        return (
            prefix
            + f'<span color="{COLOR_GRAY}" font_desc="{font_family} {label_size}">'
            + "--</span>"
        )

    reset_5 = ""
    if data.r5:
        reset_5 = (
            f'<span color="#777777" font_desc="{font_family} {reset_size}">'
            f" {escape_markup_text(data.r5)}</span>"
        )
    reset_7 = ""
    if data.r7:
        reset_7 = (
            f'<span color="#777777" font_desc="{font_family} {reset_size}">'
            f" {escape_markup_text(data.r7)}</span>"
        )

    return (
        prefix
        + f'<span color="#aaaaaa" font_desc="{font_family} {label_size}">5h </span>'
        + f'<span color="{escape_markup_attr(data.c5)}" '
        f'font_desc="{font_family} Bold {font_size}">'
        f"{escape_markup_text(data.pct5)}</span>{reset_5}"
        + f'<span color="#666666" font_desc="{font_family} {spacer_size}">   </span>'
        + f'<span color="#aaaaaa" font_desc="{font_family} {label_size}">7d </span>'
        + f'<span color="{escape_markup_attr(data.c7)}" '
        f'font_desc="{font_family} Bold {font_size}">'
        f"{escape_markup_text(data.pct7)}</span>{reset_7}"
    )


def build_overlay_markup(
    claude_data: OverlayDisplayData | None,
    openai_data: OverlayDisplayData | None,
    config: AppConfig,
) -> str:
    lines: list[str] = []
    if "claude" in config.providers:
        lines.append(build_provider_line("✦", config.color_claude, claude_data, config))
    if "openai" in config.providers:
        lines.append(build_provider_line("◆", config.color_openai, openai_data, config))
    return "\n".join(lines)
