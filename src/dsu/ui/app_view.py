"""Root coordinator widget — wires the Application to all UI parts."""

from __future__ import annotations

import asyncio
import logging
import threading

import flet as ft

from dsu.app import Application
from dsu.domain.events import DevLstEvent
from dsu.domain.models import Device
from dsu.net.locator import LocatorCmd
from dsu.ui.confirm import show_confirm
from dsu.ui.device_table import DeviceTable
from dsu.ui.flash_state import FlashState
from dsu.ui.inspector import Inspector
from dsu.ui.log_panel import LogPanel
from dsu.ui.menu import build_menu
from dsu.ui.tabs.firmware_tab import FirmwareTabState
from dsu.ui.tabs.settings_tab import SettingsForm
from dsu.ui.toast import show_toast
from dsu.ui.toolbar import build_toolbar


_LOG = logging.getLogger(__name__)


def _run_on_page(page: ft.Page, fn) -> None:
    """Schedule *fn* (a zero-arg callable) on the Flet event-loop thread.

    Flet 0.84 removed ``page.run_thread_safe``.  We use
    ``asyncio.run_coroutine_threadsafe`` against ``page.loop`` instead,
    wrapping the synchronous callable in a trivial coroutine.
    """
    async def _coro():
        fn()

    try:
        asyncio.run_coroutine_threadsafe(_coro(), page.loop)
    except Exception:
        # page not yet attached to a session (e.g. during tests) — ignore
        pass


class AppView:
    def __init__(self, page: ft.Page, app: Application) -> None:
        self._page = page
        self._app = app
        self._online: set[str] = set()
        self._online_lock = threading.Lock()
        self._flash = FlashState()

        self._table = DeviceTable(
            flash_state=self._flash,
            is_online=self._is_online,
            on_select=self._on_device_selected,
        )
        self._inspector = Inspector(
            is_online=self._is_online,
            flash_state=self._flash,
            on_action=self._on_action,
            on_apply_settings=self._on_apply_settings,
            on_pick_firmware=self._on_pick_firmware,
            on_flash_firmware=self._on_flash_firmware,
        )
        self._log = LogPanel()
        self._file_picker = ft.FilePicker()
        page.overlay.append(self._file_picker)

        toolbar = build_toolbar(
            on_search_change=self._table.set_query,
            on_theme_toggle=self._toggle_theme,
            on_menu_open=lambda _e: self._open_menu(),
        )
        self._menu = build_menu(
            on_refresh=self._refresh,
            on_settings=self._open_settings,
            on_about=self._open_about,
            on_toggle_log=self._log.toggle,
            on_add_test_devices=self._add_test_devices,
            on_exit=self._exit,
        )

        # Subscribe to events
        app.events.bind(self._on_event_threadsafe,
                        [DevLstEvent.APPEND_DEV, DevLstEvent.REMOVE_DEV,
                         DevLstEvent.UPDATE_DEV, DevLstEvent.POLL_RESPONSE,
                         DevLstEvent.CMD_RESPONSE, DevLstEvent.CON_FAIL])

        self._flash.subscribe(self._on_flash_changed)

        self.control = ft.Column(
            spacing=0, expand=True,
            controls=[
                ft.Row(controls=[toolbar, self._menu], spacing=0),
                ft.Container(content=self._table.control, expand=True),
                self._log.control,
                self._inspector.control,
            ],
        )

        # Initial population
        self._refresh_table_from_registry()

    # ---- thread-safe event marshalling ------------------------------------

    def _on_event_threadsafe(self, event: DevLstEvent, **kw) -> None:
        dev = kw.get("dev")
        _run_on_page(self._page, lambda: self._handle_event(event, dev))

    def _handle_event(self, event: DevLstEvent, dev: Device | None) -> None:
        if event == DevLstEvent.APPEND_DEV and dev is not None:
            with self._online_lock:
                self._online.add(self._key(dev))
            self._refresh_table_from_registry()
        elif event == DevLstEvent.REMOVE_DEV and dev is not None:
            with self._online_lock:
                self._online.discard(self._key(dev))
            self._refresh_table_from_registry()
            if self._inspector.device() and \
               self._key(self._inspector.device()) == self._key(dev):
                self._inspector.hide()
        elif event in (DevLstEvent.UPDATE_DEV, DevLstEvent.POLL_RESPONSE):
            if dev is not None:
                with self._online_lock:
                    self._online.add(self._key(dev))
            self._refresh_table_from_registry()
            self._inspector.refresh()
        elif event == DevLstEvent.CON_FAIL and dev is not None:
            with self._online_lock:
                self._online.discard(self._key(dev))
            self._log.add(f"{dev.name or dev.ip}: connection lost", "warn")
            show_toast(self._page,
                       f"{dev.name or dev.ip} is offline", kind="error")
            self._refresh_table_from_registry()
        elif event == DevLstEvent.CMD_RESPONSE and dev is not None:
            self._log.add(f"{dev.name or dev.ip}: cmd ok", "info")

    # ---- helpers ----------------------------------------------------------

    def _refresh_table_from_registry(self) -> None:
        self._table.set_devices(list(self._app.registry))

    def _is_online(self, dev: Device) -> bool:
        with self._online_lock:
            return self._key(dev) in self._online

    @staticmethod
    def _key(dev: Device) -> str:
        return dev.s_num or f"{dev.ip}:{dev.port}"

    # ---- toolbar/menu actions ---------------------------------------------

    def _toggle_theme(self) -> None:
        order = [ft.ThemeMode.SYSTEM, ft.ThemeMode.LIGHT, ft.ThemeMode.DARK]
        cur = self._page.theme_mode or ft.ThemeMode.SYSTEM
        idx = order.index(cur) if cur in order else 0
        self._page.theme_mode = order[(idx + 1) % len(order)]
        self._page.update()

    def _open_menu(self) -> None:
        # PopupMenuButton manages its own opening when clicked
        pass

    def _refresh(self) -> None:
        # Locator.refresh() is added in Task 14; guarded to avoid AttributeError
        if hasattr(self._app.locator, "refresh"):
            self._app.locator.refresh()
        show_toast(self._page, "Refresh requested", kind="info")

    def _open_settings(self) -> None:
        import os, sys
        path = self._app.config.devices_ini_path
        if path is None:
            show_toast(self._page,
                       "No external config file (using packaged defaults)",
                       "info")
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(path))  # type: ignore[attr-defined]
            else:
                import subprocess
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            show_toast(self._page, f"Cannot open settings: {exc}", "error")

    def _open_about(self) -> None:
        from dsu import __version__
        show_toast(self._page, f"DSU {__version__}", "info")

    def _add_test_devices(self, count: int) -> None:
        from dsu.domain.models import Device
        for i in range(count):
            self._app.registry.add(
                Device.from_address(f"10.99.0.{i + 1}", 1775))
        show_toast(self._page, f"Added {count} test device(s)", "info")

    def _exit(self) -> None:
        self._app.shutdown()
        # page.window.destroy() is async in Flet 0.84; schedule via run_task
        self._page.run_task(self._page.window.destroy)

    # ---- inspector wiring -------------------------------------------------

    def _on_device_selected(self, dev: Device) -> None:
        self._inspector.show(dev)

    def _on_action(self, key: str, dev: Device) -> None:
        names = {"reboot": "Reboot",
                 "bootloader": "Goto Bootloader",
                 "normal": "Goto Normal mode"}
        cmd = names[key]

        def do():
            if key == "reboot":
                self._send_eludp(dev, b"\x02")
            elif key == "bootloader":
                self._send_eludp(dev, b"\x06")
            elif key == "normal":
                self._send_eludp(dev, b"\x05")
            self._log.add(f"{dev.name or dev.ip}: {cmd} sent", "info")

        show_confirm(
            self._page,
            f"Send {cmd} to {dev.name or dev.ip}? Connection may be lost.",
            confirm_label=cmd,
            on_yes=do,
        )

    def _send_eludp(self, dev: Device, cmd_byte: bytes) -> None:
        self._app.controller.send_eludp(dev, cmd_byte)

    def _on_apply_settings(self, dev: Device, form: SettingsForm) -> None:
        def do():
            try:
                arr = dev.primary_settings_array(form.values())
            except Exception as exc:
                show_toast(self._page, f"Invalid settings: {exc}", "error")
                return
            self._app.controller.send_locator(
                dev, LocatorCmd.SET_PRIMARY, arr)
            show_toast(self._page, "Settings applied", "success")
            self._log.add(f"{dev.name or dev.ip}: settings applied", "info")

        show_confirm(
            self._page,
            f"Apply new settings to {dev.name or dev.ip}? "
            "Wrong IP may make device unreachable.",
            confirm_label="Apply",
            on_yes=do,
        )

    def _on_pick_firmware(self, dev: Device, fw_state: FirmwareTabState) -> None:
        async def _pick():
            files = await self._file_picker.pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["bin", "fw"],
            )
            if files:
                fw_state.path = files[0].path
                self._inspector.refresh()
        self._page.run_task(_pick)

    def _on_flash_firmware(self, dev: Device, path: str) -> None:
        from dsu.net.firmware import Firmware

        def do():
            fw = Firmware(path)
            if not fw.is_valid:
                show_toast(self._page, "Invalid firmware file", "error")
                return
            key = self._key(dev)
            total = fw.size
            self._flash.start(key, total)

            def runner():
                flash_ok = True
                flash_err: Exception | None = None
                try:
                    for pack in fw:
                        self._app.controller.send_eludp(dev, pack)
                        _run_on_page(
                            self._page,
                            lambda p=fw.progress(): self._flash.update(key, p))
                except Exception as exc:
                    flash_ok = False
                    flash_err = exc
                    _LOG.exception("flash failed for %s", key)
                finally:
                    _run_on_page(self._page, lambda: self._flash.finish(key))
                    if flash_ok:
                        _run_on_page(
                            self._page,
                            lambda: show_toast(
                                self._page,
                                f"Flash finished for {dev.name or dev.ip}",
                                "success"))
                    else:
                        err_text = f"Flash failed for {dev.name or dev.ip}: {flash_err}"
                        _run_on_page(
                            self._page,
                            lambda: show_toast(self._page, err_text, "error"))

            threading.Thread(target=runner, daemon=True,
                             name=f"flash:{key}").start()

        show_confirm(
            self._page,
            f"Flash {path} to {dev.name or dev.ip}? Do not power off.",
            confirm_label="Flash",
            on_yes=do,
        )

    # ---- flash state listener ---------------------------------------------

    def _on_flash_changed(self) -> None:
        _run_on_page(self._page, self._inspector.refresh)
