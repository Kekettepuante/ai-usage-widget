from ai_usage_widget.formatting import (
    escape_markup_attr,
    escape_markup_text,
    relative_parts,
)


def test_relative_parts_handles_multiple_ranges():
    assert relative_parts(0) == "any moment"
    assert relative_parts(59 * 60) == "59m"
    assert relative_parts(2 * 3600 + 15 * 60) == "2h 15m"
    assert relative_parts(2 * 86400 + 3 * 3600) == "2d 3h"


def test_markup_escaping_covers_text_and_attributes():
    assert escape_markup_text("<b>boom</b>") == "&lt;b&gt;boom&lt;/b&gt;"
    assert escape_markup_attr('Sans "Mono"') == "Sans &quot;Mono&quot;"
