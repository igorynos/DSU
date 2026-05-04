"""Bottom inspector — header (status, name, Actions ▾, collapse) + 3 tabs."""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from dsu.domain.models import Device
from dsu.ui.flash_state import FlashState
from dsu.ui.tabs.firmware_tab import (
    FirmwareTabState, build_firmware_tab,
)
from dsu.ui.tabs.info_tab import build_info_tab
from dsu.ui.tabs.settings_tab import (
    SettingsForm, build_settings_tab,
)


class Inspector:
    def __init__(
        self,
        *,
        is_online: Callable[[Device], bool],
        flash_state: FlashState,
        on_action: Callable[[str, Device], None],
        on_apply_settings: Callable[[Device, SettingsForm], None],
        on_pick_firmware: Callable[[Device, FirmwareTabState], None],
        on_flash_firmware: Callable[[Device, str], None],
    ) -> None:
        self._is_online = is_online
        self._flash = flash_state
        self._on_action = on_action
        self._on_apply = on_apply_settings
        self._on_pick = on_pick_firmware
        self._on_flash = on_flash_firmware

        self._device: Device | None = None
        self._fw_state = FirmwareTabState()
        self._tab_index = 0

        self._body = ft.Container(content=ft.Container())
        self.control = ft.Container(
            visible=False,
            border=ft.border.only(top=ft.BorderSide(2, "#333")),
            bgcolor="#252525",
            content=ft.Column(controls=[self._build_header(), self._body],
                              spacing=0, tight=True),
        )

    def show(self, dev: Device) -> None:
        self._device = dev
        self._fw_state = FirmwareTabState()
        self._tab_index = 0
        self.control.visible = True
        self._rebuild()

    def hide(self) -> None:
        self.control.visible = False
        self._device = None
        if self.control.page is not None:
            self.control.update()

    def refresh(self) -> None:
        if self._device is not None:
            self._rebuild()

    def device(self) -> Device | None:
        return self._device

    def fw_state(self) -> FirmwareTabState:
        return self._fw_state

    # internal --------------------------------------------------------------

    def _build_header(self) -> ft.Container:
        self._dot = ft.Text("●", size=14, color="#666")
        self._title = ft.Text("", weight=ft.FontWeight.W_600, size=13)
        self._subtitle = ft.Text("", size=11, color="#888")
        self._tabs_row = ft.Row(spacing=14)

        actions = ft.PopupMenuButton(
            content=ft.Container(
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                border=ft.border.all(1, "#333"), border_radius=4,
                content=ft.Row(controls=[
                    ft.Text("Actions", size=11),
                    ft.Icon(ft.Icons.ARROW_DROP_DOWN, size=14),
                ], spacing=2),
            ),
            items=[
                ft.PopupMenuItem(content="Reboot",
                    on_click=lambda _: self._fire_action("reboot")),
                ft.PopupMenuItem(content="Goto Bootloader",
                    on_click=lambda _: self._fire_action("bootloader")),
                ft.PopupMenuItem(content="Goto Normal mode",
                    on_click=lambda _: self._fire_action("normal")),
            ],
        )

        collapse_btn = ft.IconButton(
            icon=ft.Icons.KEYBOARD_ARROW_DOWN, tooltip="Collapse",
            on_click=lambda _: self.hide(),
        )

        return ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=4),
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Row(
                        controls=[
                            self._dot,
                            self._title,
                            self._subtitle,
                            ft.Container(expand=True),
                            actions,
                            collapse_btn,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self._tabs_row,
                ],
            ),
        )

    def _rebuild(self) -> None:
        dev = self._device
        if dev is None:
            return
        online = self._is_online(dev)
        self._dot.color = "#4ade80" if online else "#666"
        self._title.value = dev.name or "(unnamed)"
        self._subtitle.value = f"{dev.ip}  \u00b7  {dev.model}"
        self._tabs_row.controls = self._build_tab_buttons()

        body = self._build_body(dev)
        self._body.content = body
        if self.control.page is not None:
            self.control.update()

    def _build_tab_buttons(self) -> list[ft.Control]:
        labels = ["Info", "Settings", "Firmware"]
        ctrls: list[ft.Control] = []
        for i, label in enumerate(labels):
            active = i == self._tab_index
            ctrls.append(ft.Container(
                padding=ft.padding.only(top=6, bottom=4),
                border=ft.border.only(
                    bottom=ft.BorderSide(2 if active else 0, "#4a9eff")),
                content=ft.Text(
                    label,
                    size=12,
                    weight=ft.FontWeight.W_600 if active else ft.FontWeight.NORMAL,
                    color=None if active else "#888",
                ),
                on_click=lambda _e, idx=i: self._select_tab(idx),
            ))
        return ctrls

    def _select_tab(self, idx: int) -> None:
        self._tab_index = idx
        self._rebuild()

    def _build_body(self, dev: Device) -> ft.Control:
        if self._tab_index == 0:
            return build_info_tab(dev)
        if self._tab_index == 1:
            return build_settings_tab(
                dev, on_apply=lambda f: self._on_apply(dev, f))

        key = self._device_key(dev)
        flashing = self._flash.is_flashing(key)
        cur, tot = self._flash.progress(key)
        pct = (cur / tot) if tot else 0.0
        prog_text = f"{cur} of {tot} bytes" if flashing else ""
        return build_firmware_tab(
            dev,
            state=self._fw_state,
            is_flashing=flashing,
            progress_value=pct,
            progress_text=prog_text,
            on_pick_file=lambda: self._on_pick(dev, self._fw_state),
            on_flash=lambda path: self._on_flash(dev, path),
        )

    def _fire_action(self, key: str) -> None:
        if self._device is not None:
            self._on_action(key, self._device)

    @staticmethod
    def _device_key(dev: Device) -> str:
        return dev.s_num or f"{dev.ip}:{dev.port}"
