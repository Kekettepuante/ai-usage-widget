"""Main GTK application."""

from __future__ import annotations

import sys
import threading
import time
from datetime import datetime

import gi

from .config import AppConfig, load_config
from .constants import APP_NAME
from .markup import overlay_display_from_usage, overlay_error_display
from .models import ClaudeSubscriptionInfo, ProviderState, ProviderUsage
from .notifications import NotificationTracker
from .providers import (
    RateLimitError,
    fetch_claude_usage,
    fetch_openai_usage,
    load_claude_subscription_info,
    load_claude_token,
    load_openai_token,
    normalize_claude_usage,
    normalize_openai_usage,
    save_claude_token,
)
from .ui import OverlayWindow, TokenDialog, UsageDetailWindow

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Notify", "0.7")
from gi.repository import Gdk, GLib, Gtk, Notify  # noqa: E402


class UsageApp:
    def __init__(self):
        self.config: AppConfig = load_config()

        self.claude_token: str | None = None
        self.claude_usage: ProviderUsage | None = None
        self.claude_sub_info: ClaudeSubscriptionInfo | None = None
        self.claude_status = ProviderState.NO_TOKEN

        self.openai_token: str | None = None
        self.openai_account_id: str | None = None
        self.openai_usage: ProviderUsage | None = None
        self.openai_status = ProviderState.NO_TOKEN

        self.last_updated = "never"
        self.running = True
        self.overlays: list[OverlayWindow] = []
        self.notifications = NotificationTracker()

        Notify.init(APP_NAME)
        self.context_menu = self._build_menu()
        self._create_overlays()

        display = Gdk.Display.get_default()
        if display is None:
            raise RuntimeError(
                "No GTK display detected. Run the widget inside a Wayland session."
            )

        display.connect(
            "monitor-added",
            lambda *_: GLib.timeout_add(500, self._recreate_overlays),
        )
        display.connect(
            "monitor-removed",
            lambda *_: GLib.timeout_add(500, self._recreate_overlays),
        )

        if "claude" in self.config.providers:
            self.claude_token = load_claude_token()
            self.claude_sub_info = load_claude_subscription_info()
            self.claude_status = (
                ProviderState.CONNECTED if self.claude_token else ProviderState.NO_TOKEN
            )
        if "openai" in self.config.providers:
            self.openai_token, self.openai_account_id = load_openai_token()
            self.openai_status = (
                ProviderState.CONNECTED if self.openai_token else ProviderState.NO_TOKEN
            )

        if "claude" in self.config.providers and not self.claude_token:
            GLib.timeout_add_seconds(2, self._prompt_token)

        self.poll_thread = threading.Thread(target=self._poll, daemon=True)
        self.poll_thread.start()

    def _build_menu(self):
        menu = Gtk.Menu()
        for label, callback in (
            ("Show Details...", self.on_show_details),
            ("Refresh Now", lambda _: self.force_refresh()),
        ):
            item = Gtk.MenuItem(label=label)
            item.connect("activate", callback)
            menu.append(item)

        if "claude" in self.config.providers:
            menu.append(Gtk.SeparatorMenuItem())
            item = Gtk.MenuItem(label="Set Claude Token...")
            item.connect("activate", self.on_set_token)
            menu.append(item)

        menu.append(Gtk.SeparatorMenuItem())
        item = Gtk.MenuItem(label="Quit")
        item.connect("activate", self.on_quit)
        menu.append(item)
        menu.show_all()
        return menu

    def _create_overlays(self) -> None:
        display = Gdk.Display.get_default()
        if display is None:
            raise RuntimeError(
                "No GTK display detected. Run the widget inside a Wayland session."
            )
        for monitor_index in range(display.get_n_monitors()):
            monitor = display.get_monitor(monitor_index)
            self.overlays.append(OverlayWindow(monitor, self, self.config))

    def _recreate_overlays(self):
        for overlay in self.overlays:
            overlay.destroy()
        self.overlays.clear()
        self._create_overlays()
        self._update_ui()
        return False

    def _prompt_token(self):
        if not self.claude_token:
            self.on_set_token(None)
        return False

    def _poll(self) -> None:
        claude_backoff_until = 0.0
        openai_backoff_until = 0.0

        while self.running:
            now = time.time()

            if "claude" in self.config.providers and now >= claude_backoff_until:
                self._poll_claude()
                if self.claude_status is ProviderState.RATE_LIMITED:
                    claude_backoff_until = now + 600

            if "openai" in self.config.providers and now >= openai_backoff_until:
                self._poll_openai()
                if self.openai_status is ProviderState.RATE_LIMITED:
                    openai_backoff_until = now + 600

            GLib.idle_add(self._update_ui)
            time.sleep(self.config.refresh_interval)

    def _poll_claude(self) -> None:
        try:
            fresh_token = load_claude_token()
            if fresh_token:
                self.claude_token = fresh_token
            if not self.claude_token:
                self.claude_status = ProviderState.NO_TOKEN
                self.claude_usage = None
                return

            raw = fetch_claude_usage(self.claude_token)
            normalized = normalize_claude_usage(raw)
            if normalized is None:
                self.claude_status = ProviderState.ERROR
                self.claude_usage = None
                return
            self.claude_usage = normalized
            self.claude_status = ProviderState.CONNECTED
        except RateLimitError:
            print("[ai-usage] Claude rate limited, backing off 10 min", file=sys.stderr)
            self.claude_status = ProviderState.RATE_LIMITED
            self.claude_usage = None
        except Exception as exc:
            print(f"[ai-usage] Claude poll error: {exc}", file=sys.stderr)
            self.claude_status = ProviderState.ERROR
            self.claude_usage = None

    def _poll_openai(self) -> None:
        try:
            token, account_id = load_openai_token()
            if token:
                self.openai_token = token
                self.openai_account_id = account_id
            if not self.openai_token:
                self.openai_status = ProviderState.NO_TOKEN
                self.openai_usage = None
                return

            raw = fetch_openai_usage(self.openai_token, self.openai_account_id)
            normalized = normalize_openai_usage(raw)
            if normalized is None:
                self.openai_status = ProviderState.ERROR
                self.openai_usage = None
                return
            self.openai_usage = normalized
            self.openai_status = ProviderState.CONNECTED
        except RateLimitError:
            print("[ai-usage] OpenAI rate limited, backing off 10 min", file=sys.stderr)
            self.openai_status = ProviderState.RATE_LIMITED
            self.openai_usage = None
        except Exception as exc:
            print(f"[ai-usage] OpenAI poll error: {exc}", file=sys.stderr)
            self.openai_status = ProviderState.ERROR
            self.openai_usage = None

    def force_refresh(self) -> None:
        def _refresh():
            if "claude" in self.config.providers:
                self._poll_claude()
            if "openai" in self.config.providers:
                self._poll_openai()
            GLib.idle_add(self._update_ui)

        threading.Thread(target=_refresh, daemon=True).start()

    def _update_ui(self):
        self.last_updated = datetime.now().strftime("%H:%M:%S")

        claude_overlay = overlay_display_from_usage(self.claude_usage, self.config)
        if claude_overlay is None and self.claude_status in {
            ProviderState.ERROR,
            ProviderState.RATE_LIMITED,
        }:
            claude_overlay = overlay_error_display()

        openai_overlay = overlay_display_from_usage(self.openai_usage, self.config)
        if openai_overlay is None and self.openai_status in {
            ProviderState.ERROR,
            ProviderState.RATE_LIMITED,
        }:
            openai_overlay = overlay_error_display()

        for overlay in self.overlays:
            overlay.update(claude_overlay, openai_overlay)

        if self.config.notifications:
            self._emit_notifications()
        return False

    def _emit_notifications(self) -> None:
        dominant = 0.0
        if self.claude_usage:
            dominant = max(
                dominant,
                self.claude_usage.five_hour.dec,
                self.claude_usage.seven_day.dec,
            )
        if self.openai_usage:
            dominant = max(
                dominant,
                self.openai_usage.five_hour.dec,
                self.openai_usage.seven_day.dec,
            )

        if not self.notifications.startup_sent:
            self.notifications.startup_sent = True
            parts: list[str] = []
            if self.claude_usage:
                parts.append(
                    "Claude: "
                    f"5h {self.claude_usage.five_hour.pct}% | "
                    f"7d {self.claude_usage.seven_day.pct}%"
                )
            if self.openai_usage:
                parts.append(
                    "OpenAI: "
                    f"5h {self.openai_usage.five_hour.pct}% | "
                    f"7d {self.openai_usage.seven_day.pct}%"
                )
            Notify.Notification.new(
                APP_NAME,
                "\n".join(parts) if parts else "Waiting for data...",
                "dialog-information",
            ).show()
            return

        threshold = self.notifications.next_threshold_notification(dominant)
        if threshold is None:
            return

        messages = {
            75: ("Usage: 75%", "Approaching rate limits.", Notify.Urgency.NORMAL),
            90: ("Usage: 90%", "Close to rate limits!", Notify.Urgency.CRITICAL),
            100: ("Usage: 100%", "Rate limit reached!", Notify.Urgency.CRITICAL),
        }
        title, message, urgency = messages[threshold]
        notification = Notify.Notification.new(title, message, "dialog-warning")
        notification.set_urgency(urgency)
        notification.show()

    def on_show_details(self, _widget) -> None:
        UsageDetailWindow(
            self.config,
            self.claude_usage,
            self.openai_usage,
            self.last_updated,
            self.claude_status,
            self.openai_status,
            claude_info=self.claude_sub_info,
            app_ref=self,
        )

    def on_set_token(self, _widget) -> None:
        dialog = TokenDialog()
        if dialog.run() == Gtk.ResponseType.OK:
            token = dialog.get_token()
            if token:
                self.claude_token = token
                self.claude_status = ProviderState.CONNECTED
                save_claude_token(token)
                self.force_refresh()
        dialog.destroy()

    def on_quit(self, _widget) -> None:
        self.running = False
        Notify.uninit()
        Gtk.main_quit()

    def run(self) -> None:
        Gtk.main()


def main() -> int:
    try:
        app = UsageApp()
    except RuntimeError as exc:
        print(f"[ai-usage] {exc}", file=sys.stderr)
        return 1
    app.run()
    return 0
