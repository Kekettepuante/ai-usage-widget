#!/usr/bin/env bash
set -euo pipefail

APP_ID="ai-usage-widget"
LEGACY_APP_ID="claude-usage-widget"

echo "AI Usage Widget — Uninstaller"
echo "=============================="

pkill -f "$HOME/.local/share/ai-usage-widget/[a]i_usage_widget.py" 2>/dev/null || true
pkill -f "[c]laude_usage_widget.py" 2>/dev/null || true

rm -rf "$HOME/.local/share/$APP_ID"
rm -rf "$HOME/.local/share/$LEGACY_APP_ID"
rm -f "$HOME/.local/bin/ai-widget-start"
rm -f "$HOME/.local/bin/ai-widget-stop"
rm -f "$HOME/.local/bin/claude-widget-start"
rm -f "$HOME/.local/bin/claude-widget-stop"
rm -f "$HOME/.local/bin/claude-usage-widget"
rm -f "$HOME/.config/autostart/$APP_ID.desktop"
rm -f "$HOME/.config/autostart/$LEGACY_APP_ID.desktop"
rm -f "$HOME/.local/share/applications/$APP_ID.desktop"

read -rp "Remove config (~/.config/$APP_ID)? [y/N] " yn
case "${yn,,}" in
    y|yes) rm -rf "$HOME/.config/$APP_ID"; echo "Config removed" ;;
    *) echo "Config preserved" ;;
esac

echo "Uninstalled."
