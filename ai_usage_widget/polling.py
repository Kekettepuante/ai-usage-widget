"""Polling state helpers."""

from __future__ import annotations

from .models import ProviderState, ProviderUsage


def resolve_success(
    normalized: ProviderUsage | None,
) -> tuple[ProviderUsage | None, ProviderState]:
    if normalized is None:
        return None, ProviderState.ERROR
    return normalized, ProviderState.CONNECTED


def resolve_rate_limited(
    previous_usage: ProviderUsage | None,
) -> tuple[ProviderUsage | None, ProviderState]:
    return previous_usage, ProviderState.RATE_LIMITED
