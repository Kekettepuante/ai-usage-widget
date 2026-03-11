from ai_usage_widget.models import ProviderState, ProviderUsage, UsageBucket
from ai_usage_widget.polling import resolve_rate_limited, resolve_success


def _usage() -> ProviderUsage:
    return ProviderUsage(
        five_hour=UsageBucket(32, 0.32, "16:00", "1h 20m"),
        seven_day=UsageBucket(33, 0.33, "dem. 12:00", "1d 3h"),
    )


def test_resolve_success_sets_connected_state():
    usage = _usage()

    next_usage, status = resolve_success(usage)

    assert next_usage == usage
    assert status is ProviderState.CONNECTED


def test_resolve_success_treats_missing_payload_as_error():
    next_usage, status = resolve_success(None)

    assert next_usage is None
    assert status is ProviderState.ERROR


def test_resolve_rate_limited_keeps_last_known_usage():
    usage = _usage()

    next_usage, status = resolve_rate_limited(usage)

    assert next_usage == usage
    assert status is ProviderState.RATE_LIMITED


def test_resolve_rate_limited_allows_empty_snapshot():
    next_usage, status = resolve_rate_limited(None)

    assert next_usage is None
    assert status is ProviderState.RATE_LIMITED
