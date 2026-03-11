from ai_usage_widget.config import AppConfig, load_config


def test_load_config_creates_default_file(tmp_path):
    config_file = tmp_path / "config.json"

    config = load_config(config_file)

    assert config == AppConfig()
    assert config_file.exists()


def test_load_config_sanitizes_invalid_values(tmp_path, capsys):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        """
        {
          "providers": ["claude", "bogus", "claude"],
          "position": "middle",
          "margin_x": -10,
          "font_family": "",
          "threshold_medium": 95,
          "threshold_high": 70,
          "threshold_critical": 60,
          "refresh_interval": -5,
          "notifications": "yes"
        }
        """
    )

    config = load_config(config_file)

    assert config.providers == ("claude",)
    assert config.position == "top-right"
    assert config.margin_x == 10
    assert config.font_family == "Sans"
    assert config.threshold_medium == 50
    assert config.threshold_high == 75
    assert config.threshold_critical == 90
    assert config.refresh_interval == 120
    assert config.notifications is True
    assert "Invalid config" in capsys.readouterr().err
