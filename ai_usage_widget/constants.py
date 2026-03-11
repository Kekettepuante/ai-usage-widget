"""Project constants and default paths."""

from pathlib import Path

APP_ID = "ai-usage-widget"
APP_NAME = "AI Usage Widget"

CLAUDE_API_URL = "https://api.anthropic.com/api/oauth/usage"
CLAUDE_CREDENTIALS = Path.home() / ".claude" / ".credentials.json"

OPENAI_API_URL = "https://chatgpt.com/backend-api/wham/usage"
OPENAI_AUTH_FILE = Path.home() / ".codex" / "auth.json"

CONFIG_DIR = Path.home() / ".config" / APP_ID
CONFIG_FILE = CONFIG_DIR / "config.json"

VALID_PROVIDERS = ("claude", "openai")
VALID_POSITIONS = ("top-right", "top-left", "bottom-right", "bottom-left")
