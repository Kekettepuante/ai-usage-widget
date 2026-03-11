"""Formatting helpers used by providers and UI."""

from __future__ import annotations

from datetime import datetime, timezone
from html import escape


def escape_markup_text(value: object) -> str:
    return escape(str(value), quote=False)


def escape_markup_attr(value: object) -> str:
    return escape(str(value), quote=True)


def relative_parts(total_sec: int) -> str:
    if total_sec <= 0:
        return "any moment"
    days, remainder = divmod(total_sec, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    if days > 0:
        return f"{days}d {hours}h"
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def absolute_display(local_dt: datetime) -> str:
    now = datetime.now().astimezone()
    if local_dt.date() == now.date():
        return local_dt.strftime("%H:%M")
    if (local_dt.date() - now.date()).days == 1:
        return "dem. " + local_dt.strftime("%H:%M")
    return local_dt.strftime("%d/%m %H:%M")


def format_reset_time(iso_str: str | None) -> str:
    if not iso_str:
        return "unknown"
    try:
        reset_dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        delta = reset_dt - datetime.now(timezone.utc)
        return relative_parts(int(delta.total_seconds()))
    except Exception:
        return iso_str


def format_reset_time_unix(ts: int | float | None) -> str:
    if not ts:
        return "unknown"
    try:
        reset_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        delta = reset_dt - datetime.now(timezone.utc)
        return relative_parts(int(delta.total_seconds()))
    except Exception:
        return "?"


def format_reset_datetime(iso_str: str | None) -> str:
    if not iso_str:
        return "?"
    try:
        reset_dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return absolute_display(reset_dt.astimezone())
    except Exception:
        return "?"


def format_reset_datetime_unix(ts: int | float | None) -> str:
    if not ts:
        return "?"
    try:
        reset_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return absolute_display(reset_dt.astimezone())
    except Exception:
        return "?"
