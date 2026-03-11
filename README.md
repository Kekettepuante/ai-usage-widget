# AI Usage Widget

Lightweight Wayland overlay that shows your **Claude** and **OpenAI/Codex** usage (5h + 7d rate-limit windows) as transparent text pinned to a screen corner.

![Screenshot](screenshot.png)

Built with Python, GTK3, and gtk-layer-shell. No Electron, no browser, no tray icon — just text on your desktop.

This repository is the clean public baseline of the project.

## Install

```bash
# Dependencies (Debian/Ubuntu)
sudo apt install python3 python3-gi python3-gi-cairo gir1.2-notify-0.7 gir1.2-gtklayershell-0.1

# Install
git clone https://github.com/Kekettepuante/ai-usage-widget.git && cd ai-usage-widget
./install.sh

# Start
ai-widget-start
```

It autostarts on login.

## What it shows

```
✦ 5h 42%  15:30   7d 12%  dem. 09:00    ← Claude (Anthropic)
◆ 5h  8%  14:15   7d  3%  13/03 11:00   ← OpenAI (Codex)
```

- Percentage = current usage of the rate-limit window
- Time = when the window resets
- Colors change from green → yellow → orange → red as usage increases

Left-click opens a detail popup. Right-click opens a context menu.

## Credentials

**Claude** — auto-detected from `~/.claude/.credentials.json` (Claude Code). Run `claude login` if needed.

**OpenAI** — auto-detected from `~/.codex/auth.json` (Codex CLI). Run `codex` and log in if needed.

No manual token setup required if you use the CLI tools.

## Configuration

All settings are in `~/.config/ai-usage-widget/config.json` (auto-generated on first run):

```json
{
  "providers": ["claude", "openai"],
  "position": "top-right",
  "margin_x": 10,
  "margin_y": 4,
  "font_family": "Sans",
  "font_size": 11,
  "color_claude": "#D97757",
  "color_openai": "#10A37F",
  "color_low": "#22c55e",
  "color_medium": "#eab308",
  "color_high": "#f97316",
  "color_critical": "#ef4444",
  "threshold_medium": 50,
  "threshold_high": 75,
  "threshold_critical": 90,
  "refresh_interval": 120,
  "notifications": true
}
```

| Key | What it does |
|---|---|
| `providers` | Which lines to show. Remove `"openai"` for Claude-only. |
| `position` | `top-right`, `top-left`, `bottom-right`, `bottom-left` |
| `margin_x/y` | Distance from screen edge (px) |
| `font_family` / `font_size` | Overlay font |
| `color_*` | Brand and threshold colors |
| `threshold_*` | When colors change (percentage) |
| `refresh_interval` | Polling interval in seconds |
| `notifications` | Desktop alerts at 75%, 90%, 100% |

Restart the widget after editing.

## Commands

```bash
ai-widget-start    # Start
ai-widget-stop     # Stop
```

## Development

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .[dev]
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
bash validate.sh
```

## Uninstall

```bash
./uninstall.sh
```

## Requirements

- Linux with Wayland compositor (Sway, Hyprland, GNOME Wayland, etc.)
- Python 3.10+
- GTK3 + gtk-layer-shell

## How it works

Polls these APIs every 2 minutes:
- **Claude**: `GET https://api.anthropic.com/api/oauth/usage` (OAuth token from Claude Code)
- **OpenAI**: `GET https://chatgpt.com/backend-api/wham/usage` (OAuth token from Codex CLI)

Both are undocumented internal APIs used by the respective CLI tools.

## Credits

Inspired by [claude-usage-widget](https://github.com/SlavomirDurej/claude-usage-widget) by SlavomirDurej (Electron-based, cross-platform).

This is an independent rewrite in Python/GTK for Wayland, with multi-provider support.

## License

MIT — Statotech Systems
