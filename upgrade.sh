#!/usr/bin/env bash
set -euo pipefail

echo "AI Usage Widget — Upgrader"
echo "=========================="

if [ ! -f "ai_usage_widget.py" ] || [ ! -f "install.sh" ]; then
    echo "Run this from inside the cloned repository."
    exit 1
fi

echo ""
echo "Pulling latest..."
git pull

echo ""
echo "Stopping widget..."
pkill -f "$HOME/.local/share/ai-usage-widget/[a]i_usage_widget.py" 2>/dev/null && sleep 1 || true
pkill -f "[c]laude_usage_widget.py" 2>/dev/null && sleep 1 || true

echo ""
echo "Reinstalling..."
bash install.sh

echo ""
echo "Restarting..."
bash "$HOME/.local/bin/ai-widget-start"

echo ""
echo "Upgrade complete."
