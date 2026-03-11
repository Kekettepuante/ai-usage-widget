# Changelog

## [1.0.0] - 2026-03-11

Initial public release of the rewritten AI Usage Widget.

### Added
- Wayland overlay for Claude and OpenAI/Codex usage windows
- Strict config validation with defaults and safe fallbacks
- Desktop notifications at 75%, 90%, and 100% usage
- Multi-monitor overlay support via gtk-layer-shell
- Shell installer, uninstaller, upgrader, and validation script
- Unit tests, linting, formatting, and GitHub Actions CI

### Notes
- Config path: `~/.config/ai-usage-widget/config.json`
- APIs used are the same internal endpoints consumed by the CLI tools
