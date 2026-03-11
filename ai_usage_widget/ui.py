# ruff: noqa: E402, I001
"""GTK UI layer for the widget."""

from __future__ import annotations

import gi

gi.require_foreign("cairo")
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GtkLayerShell", "0.1")

import cairo

from . import __version__
from .config import AppConfig
from .constants import APP_ID, APP_NAME
from .formatting import escape_markup_attr, escape_markup_text
from .markup import build_overlay_markup, get_color_for_pct
from .models import (
    ClaudeSubscriptionInfo,
    OverlayDisplayData,
    ProviderState,
    ProviderUsage,
)

from gi.repository import Gdk, Gtk, GtkLayerShell  # noqa: E402


class OverlayWindow(Gtk.Window):
    """Transparent text overlay pinned to a monitor corner."""

    def __init__(self, monitor, app, config: AppConfig):
        super().__init__()
        self.app = app
        self.config = config

        top = "top" in config.position
        right = "right" in config.position

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_monitor(self, monitor)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, top)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, not top)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, right)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, not right)
        edge_v = GtkLayerShell.Edge.TOP if top else GtkLayerShell.Edge.BOTTOM
        edge_h = GtkLayerShell.Edge.RIGHT if right else GtkLayerShell.Edge.LEFT
        GtkLayerShell.set_margin(self, edge_v, config.margin_y)
        GtkLayerShell.set_margin(self, edge_h, config.margin_x)
        GtkLayerShell.set_namespace(self, APP_ID)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.NONE)

        self.set_app_paintable(True)
        self.set_decorated(False)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.connect("draw", self._on_draw_bg)

        self.label = Gtk.Label()
        self.label.set_xalign(1.0 if right else 0.0)
        self.label.set_justify(
            Gtk.Justification.RIGHT if right else Gtk.Justification.LEFT
        )
        self.label.set_markup(build_overlay_markup(None, None, config))

        css = Gtk.CssProvider()
        css.load_from_data(
            b"""
            * { background-color: transparent; background-image: none; }
            label {
                text-shadow: 1px 1px 3px rgba(0,0,0,0.9),
                             0px 0px 6px rgba(0,0,0,0.5);
            }
        """
        )
        self.get_style_context().add_provider(
            css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.label.get_style_context().add_provider(
            css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.add(self.label)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect("button-press-event", self._on_click)
        self.show_all()

    @staticmethod
    def _on_draw_bg(widget, cr):
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        return False

    def update(
        self,
        claude_data: OverlayDisplayData | None,
        openai_data: OverlayDisplayData | None,
    ) -> None:
        self.label.set_markup(
            build_overlay_markup(claude_data, openai_data, self.config)
        )

    def _on_click(self, widget, event):
        if event.button == 1:
            self.app.on_show_details(None)
        elif event.button == 3:
            self.app.context_menu.popup_at_pointer(event)


class UsageDetailWindow(Gtk.Window):
    """Popup showing detailed usage info for all providers."""

    def __init__(
        self,
        config: AppConfig,
        claude_usage: ProviderUsage | None,
        openai_usage: ProviderUsage | None,
        last_updated: str,
        claude_status: ProviderState,
        openai_status: ProviderState,
        claude_info: ClaudeSubscriptionInfo | None = None,
        app_ref=None,
    ):
        super().__init__(title=APP_NAME)
        self._app_ref = app_ref
        self.config = config
        self.set_default_size(380, -1)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.set_keep_above(True)
        self.connect("focus-out-event", lambda *_: self.destroy())

        css = Gtk.CssProvider()
        css.load_from_data(
            b"""
            #detail-window, #detail-window * { background-image: none; }
            #detail-window { background-color: #1a1a2e; }
            .title-label  { color: #e0e0ff; font-size: 16px; font-weight: bold; }
            .section-label { color: #a0a0c0; font-size: 11px; font-weight: bold;
                             letter-spacing: 2px; }
            .metric-sub   { color: #8888aa; font-size: 11px; }
            .reset-label  { color: #6b7280; font-size: 11px; }
            .status-ok    { color: #22c55e; font-size: 11px; }
            .status-err   { color: #ef4444; font-size: 11px; }
            .separator    { background-color: #2a2a4a; }
        """
        )
        self.set_name("detail-window")
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_top(16)
        vbox.set_margin_bottom(16)
        vbox.set_margin_start(20)
        vbox.set_margin_end(20)

        if "claude" in config.providers:
            self._add_provider_section(
                vbox,
                "✦ Claude",
                config.color_claude,
                claude_usage,
                claude_status,
                claude_info,
            )

        if "openai" in config.providers:
            title = "◆ OpenAI"
            if openai_usage and openai_usage.plan_type:
                title += f" ({openai_usage.plan_type.title()})"
            self._add_provider_section(
                vbox,
                title,
                config.color_openai,
                openai_usage,
                openai_status,
            )

        separator = Gtk.Separator()
        separator.get_style_context().add_class("separator")
        vbox.pack_start(separator, False, False, 4)

        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        updated_label = Gtk.Label(label=f"Updated: {last_updated}")
        updated_label.get_style_context().add_class("metric-sub")
        footer.pack_start(updated_label, False, False, 0)

        refresh_button = Gtk.Button(label="Refresh")
        refresh_button.set_relief(Gtk.ReliefStyle.NONE)
        refresh_css = Gtk.CssProvider()
        refresh_css.load_from_data(
            b"""
            button { color: #8888aa; background: transparent;
                     border: none; padding: 2px 8px; }
            button:hover { color: #e0e0ff; }
        """
        )
        refresh_button.get_style_context().add_provider(
            refresh_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        refresh_button.connect(
            "clicked",
            lambda _: (self.destroy(), self._app_ref and self._app_ref.force_refresh()),
        )
        footer.pack_end(refresh_button, False, False, 0)
        vbox.pack_start(footer, False, False, 0)

        version_label = Gtk.Label(label=f"v{__version__}")
        version_label.get_style_context().add_class("reset-label")
        version_label.set_halign(Gtk.Align.CENTER)
        vbox.pack_start(version_label, False, False, 0)

        self.add(vbox)
        self.show_all()

    def _add_provider_section(
        self,
        vbox,
        title_text: str,
        title_color: str,
        usage: ProviderUsage | None,
        status: ProviderState,
        info: ClaudeSubscriptionInfo | None = None,
    ) -> None:
        separator = Gtk.Separator()
        separator.get_style_context().add_class("separator")
        vbox.pack_start(separator, False, False, 4)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title = Gtk.Label()
        title.set_markup(
            f'<span foreground="{escape_markup_attr(title_color)}" '
            f'font_weight="bold" font="14">{escape_markup_text(title_text)}</span>'
        )
        header.pack_start(title, False, False, 0)

        status_label = Gtk.Label(label=f"  {status.value}")
        status_label.get_style_context().add_class(
            "status-ok" if status is ProviderState.CONNECTED else "status-err"
        )
        header.pack_end(status_label, False, False, 0)
        vbox.pack_start(header, False, False, 0)

        if info and info.subscription_type:
            plan = Gtk.Label(label=f"Plan: {info.subscription_type}")
            plan.get_style_context().add_class("metric-sub")
            plan.set_halign(Gtk.Align.START)
            vbox.pack_start(plan, False, False, 0)

        if usage:
            self._add_usage_blocks(vbox, usage)
        elif status is not ProviderState.NO_TOKEN:
            error_label = Gtk.Label(label="Unable to fetch usage data.")
            error_label.get_style_context().add_class("status-err")
            vbox.pack_start(error_label, False, False, 4)

    def _add_usage_blocks(self, vbox, usage: ProviderUsage) -> None:
        for bucket_name, label_text in (
            ("five_hour", "5-HOUR WINDOW"),
            ("seven_day", "7-DAY WINDOW"),
        ):
            bucket = getattr(usage, bucket_name)
            section_label = Gtk.Label(label=label_text)
            section_label.get_style_context().add_class("section-label")
            section_label.set_halign(Gtk.Align.START)
            vbox.pack_start(section_label, False, False, 0)

            color = get_color_for_pct(bucket.dec, self.config)
            value = Gtk.Label()
            value.set_markup(
                f'<span foreground="{escape_markup_attr(color)}" '
                f'font_weight="bold" font="28">{bucket.pct}%</span>'
            )
            value.set_halign(Gtk.Align.START)
            vbox.pack_start(value, False, False, 0)

            bar = Gtk.LevelBar()
            bar.set_min_value(0)
            bar.set_max_value(1.0)
            bar.set_value(bucket.dec)
            bar.set_size_request(-1, 8)
            for offset_name in ("low", "high", "full"):
                bar.remove_offset_value(offset_name)
            bar_css = Gtk.CssProvider()
            bar_css.load_from_data(
                f"""
                    levelbar trough {{
                        background-color: #2a2a4a; border-radius: 4px;
                        min-height: 8px;
                    }}
                    levelbar trough block.filled {{
                        background-color: {color}; border-radius: 4px;
                        min-height: 8px;
                    }}
                """.encode()
            )
            bar.get_style_context().add_provider(
                bar_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            vbox.pack_start(bar, False, False, 0)

            reset_label = Gtk.Label(label=f"Resets in {bucket.reset_relative}")
            reset_label.get_style_context().add_class("reset-label")
            reset_label.set_halign(Gtk.Align.START)
            vbox.pack_start(reset_label, False, False, 0)


class TokenDialog(Gtk.Dialog):
    def __init__(self, parent=None):
        super().__init__(title="Claude OAuth Token", transient_for=parent, flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK,
            Gtk.ResponseType.OK,
        )
        self.set_default_size(450, -1)
        box = self.get_content_area()
        box.set_spacing(8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        label = Gtk.Label()
        label.set_markup(
            "Enter your Claude OAuth token.\n"
            "<small>From <b>~/.claude/.credentials.json</b> (Claude Code) "
            "or browser DevTools.</small>"
        )
        label.set_line_wrap(True)
        box.pack_start(label, False, False, 0)

        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("sk-ant-oat01-...")
        self.entry.set_visibility(False)
        box.pack_start(self.entry, False, False, 0)
        self.show_all()

    def get_token(self) -> str:
        return self.entry.get_text().strip()
