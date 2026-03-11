#!/usr/bin/env bash
set -euo pipefail

APP_ID="ai-usage-widget"
LEGACY_APP_ID="claude-usage-widget"
INSTALL_DIR="$HOME/.local/share/$APP_ID"
SCRIPT_NAME="ai_usage_widget.py"
PACKAGE_DIR="ai_usage_widget"

echo "AI Usage Widget — Installer"
echo "============================"

# ── Dependencies ─────────────────────────────────────────────────────────────

echo ""
echo "Checking dependencies..."

MISSING=()

command -v python3 &>/dev/null || MISSING+=("python3")

python3 -c "
import gi
gi.require_version('Gtk','3.0')
gi.require_version('Notify','0.7')
gi.require_version('GtkLayerShell','0.1')
" 2>/dev/null || {
    MISSING+=("python3-gi" "gir1.2-notify-0.7" "gir1.2-gtklayershell-0.1")
}

python3 -c "import cairo" 2>/dev/null || MISSING+=("python3-gi-cairo")

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "  Missing: ${MISSING[*]}"
    read -rp "  Install now? [Y/n] " yn
    case "${yn,,}" in
        n|no) echo "Aborted."; exit 1 ;;
        *)
            sudo apt update
            sudo apt install -y "${MISSING[@]}"
            ;;
    esac
fi

echo "  All dependencies OK"

# ── Install files ────────────────────────────────────────────────────────────

echo ""
echo "Installing to $INSTALL_DIR ..."

mkdir -p "$INSTALL_DIR"
rm -rf "$INSTALL_DIR/$PACKAGE_DIR"
rm -rf "$HOME/.local/share/$LEGACY_APP_ID"
cp "$SCRIPT_NAME" "$INSTALL_DIR/$SCRIPT_NAME"
cp -r "$PACKAGE_DIR" "$INSTALL_DIR/$PACKAGE_DIR"
chmod +x "$INSTALL_DIR/$SCRIPT_NAME"

# ── Wrapper scripts ──────────────────────────────────────────────────────────

mkdir -p "$HOME/.local/bin"

cat > "$HOME/.local/bin/ai-widget-start" <<'EOFSTART'
#!/bin/bash
SCRIPT="$HOME/.local/share/ai-usage-widget/ai_usage_widget.py"
PATTERN="$HOME/.local/share/ai-usage-widget/[a]i_usage_widget.py"
LOG="/tmp/ai-usage-widget.log"

if pgrep -f "$PATTERN" >/dev/null 2>&1; then
    echo "Already running ($(pgrep -f "$PATTERN"))"
    exit 0
fi

nohup env -i \
  HOME="$HOME" \
  DISPLAY="${DISPLAY:-}" \
  WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-}" \
  XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
  DBUS_SESSION_BUS_ADDRESS="$DBUS_SESSION_BUS_ADDRESS" \
  PATH="/usr/local/bin:/usr/bin:/bin" \
  /usr/bin/python3 "$SCRIPT" > "$LOG" 2>&1 </dev/null &

sleep 1
if pgrep -f "$PATTERN" >/dev/null 2>&1; then
    echo "Widget started"
else
    echo "Failed to start. Check $LOG"
    exit 1
fi
EOFSTART

cat > "$HOME/.local/bin/ai-widget-stop" <<'EOFSTOP'
#!/bin/bash
if pkill -f "$HOME/.local/share/ai-usage-widget/[a]i_usage_widget.py" 2>/dev/null; then
    echo "Widget stopped"
else
    echo "Not running"
fi
EOFSTOP

chmod +x "$HOME/.local/bin/ai-widget-start"
chmod +x "$HOME/.local/bin/ai-widget-stop"
rm -f "$HOME/.local/bin/claude-widget-start"
rm -f "$HOME/.local/bin/claude-widget-stop"
rm -f "$HOME/.local/bin/claude-usage-widget"

echo "  Installed"

# ── Autostart ────────────────────────────────────────────────────────────────

echo ""
echo "Setting up autostart..."

AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

cat > "$AUTOSTART_DIR/$APP_ID.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=AI Usage Widget
Comment=Shows Claude and OpenAI usage as a desktop overlay
Exec=$HOME/.local/bin/ai-widget-start
Terminal=false
Categories=Utility;
StartupNotify=false
X-GNOME-Autostart-enabled=true
EOF

rm -f "$AUTOSTART_DIR/$LEGACY_APP_ID.desktop"

echo "  Autostart enabled"

# ── Check credentials ────────────────────────────────────────────────────────

echo ""
CLAUDE_CRED="$HOME/.claude/.credentials.json"
CODEX_AUTH="$HOME/.codex/auth.json"

[ -f "$CLAUDE_CRED" ] && echo "  Found Claude credentials" || echo "  No Claude credentials (run: claude login)"
[ -f "$CODEX_AUTH" ] && echo "  Found Codex credentials" || echo "  No Codex credentials (run: codex and log in)"

# ── Done ─────────────────────────────────────────────────────────────────────

echo ""
echo "Done. Run: ai-widget-start"
