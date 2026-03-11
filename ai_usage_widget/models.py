"""Typed models shared across the application."""

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True, slots=True)
class UsageBucket:
    pct: int
    dec: float
    reset_display: str
    reset_relative: str


@dataclass(frozen=True, slots=True)
class ProviderUsage:
    five_hour: UsageBucket
    seven_day: UsageBucket
    plan_type: str = ""


@dataclass(frozen=True, slots=True)
class ClaudeSubscriptionInfo:
    subscription_type: str = ""
    rate_limit_tier: str = ""


@dataclass(frozen=True, slots=True)
class OverlayDisplayData:
    pct5: str
    pct7: str
    c5: str
    c7: str
    r5: str = ""
    r7: str = ""


class ProviderState(str, Enum):
    CONNECTED = "Connected"
    NO_TOKEN = "No token"
    RATE_LIMITED = "Rate limited"
    ERROR = "Error"
