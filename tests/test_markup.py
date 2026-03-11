from ai_usage_widget.config import AppConfig
from ai_usage_widget.markup import build_provider_line, overlay_display_from_usage
from ai_usage_widget.models import ProviderUsage, UsageBucket


def test_overlay_display_uses_threshold_colors():
    config = AppConfig()
    usage = ProviderUsage(
        five_hour=UsageBucket(80, 0.8, "15:00", "2h"),
        seven_day=UsageBucket(15, 0.15, "dem. 09:00", "1d 4h"),
    )

    display = overlay_display_from_usage(usage, config)

    assert display is not None
    assert display.c5 == config.color_high
    assert display.c7 == config.color_low


def test_provider_line_escapes_markup_sensitive_values():
    config = AppConfig(font_family='Sans "Mono"<bad>')
    usage = ProviderUsage(
        five_hour=UsageBucket(80, 0.8, "<soon & now>", "2h"),
        seven_day=UsageBucket(15, 0.15, '"tomorrow"', "1d"),
    )
    display = overlay_display_from_usage(usage, config)

    markup = build_provider_line("◆", "#10A37F", display, config)

    assert "<soon & now>" not in markup
    assert "&lt;soon &amp; now&gt;" in markup
    assert 'Sans "Mono"<bad>' not in markup
    assert "Sans &quot;Mono&quot;&lt;bad&gt;" in markup
