"""Main device table — populates from DeviceRegistry, filtered by query."""

from __future__ import annotations

from collections.abc import Callable, Iterable

import flet as ft

from dsu.domain.models import Device
from dsu.ui._helpers import format_serial_short, matches_filter
from dsu.ui.flash_state import FlashState


COLUMNS = [
    ("",          0.05),  # status dot
    ("NAME",      0.14),
    ("IP : PORT", 0.12),
    ("MODEL",     0.09),
    ("S/N",       0.15),
    ("MAC",       0.14),
    ("FW",        0.07),
    ("BTLDR",     0.07),
    ("PCB",       0.07),
    ("BOOT MODE", 0.10),
]


class DeviceTable:
    def __init__(
        self,
        *,
        flash_state: FlashState,
        is_online: Callable[[Device], bool],
        on_select: Callable[[Device], None],
    ) -> None:
        self._flash = flash_state
        self._is_online = is_online
        self._on_select = on_select
        self._query: str = ""
        self._selected_key: str | None = None
        self._devices: list[Device] = []
        self._column = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
        self.control = ft.Container(
            content=ft.Column(
                controls=[self._build_header(), self._column],
                spacing=0,
                expand=True,
            ),
            expand=True,
        )

    def set_query(self, query: str) -> None:
        self._query = query
        self._render()

    def set_devices(self, devices: Iterable[Device]) -> None:
        self._devices = list(devices)
        self._render()

    def _build_header(self) -> ft.Container:
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(label, size=10, weight=ft.FontWeight.W_600),
                        expand=int(weight * 100),
                    ) for label, weight in COLUMNS
                ],
            ),
        )

    def _render(self) -> None:
        rows = []
        for dev in self._devices:
            if not matches_filter(dev, self._query):
                continue
            rows.append(self._build_row(dev))
        self._column.controls = rows
        if self._column.page is not None:
            self._column.update()

    def _build_row(self, dev: Device) -> ft.Container:
        key = self._device_key(dev)
        online = self._is_online(dev)
        is_selected = key == self._selected_key
        flashing = self._flash.is_flashing(key)
        percent = self._flash.percent(key) if flashing else 0

        dot = ft.Text("●", size=14,
                      color="#4ade80" if online else "#666666")

        name_widget: ft.Control = ft.Text(dev.name or "(unnamed)", size=12)
        if flashing:
            name_widget = ft.Column(
                controls=[
                    ft.Text(dev.name or "(unnamed)", size=12),
                    ft.ProgressBar(value=percent / 100, height=2),
                ],
                spacing=2, tight=True,
            )

        cells = [
            (dot, COLUMNS[0][1]),
            (name_widget, COLUMNS[1][1]),
            (ft.Text(f"{dev.ip}:{dev.port}", size=11), COLUMNS[2][1]),
            (ft.Text(dev.model, size=11), COLUMNS[3][1]),
            (ft.Text(format_serial_short(dev.s_num),
                     size=10, font_family="monospace",
                     tooltip=dev.s_num or None), COLUMNS[4][1]),
            (ft.Text(dev.mac, size=10, font_family="monospace"), COLUMNS[5][1]),
            (ft.Text(dev.fw, size=11), COLUMNS[6][1]),
            (ft.Text(dev.btldr, size=11), COLUMNS[7][1]),
            (ft.Text(dev.pcb, size=11), COLUMNS[8][1]),
            (ft.Text(dev.boot_mode, size=11), COLUMNS[9][1]),
        ]

        row = ft.Row(
            controls=[
                ft.Container(content=c, expand=int(w * 100))
                for c, w in cells
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor="#2d3a4d" if is_selected else None,
            on_click=lambda _e, d=dev: self._select(d),
            content=row,
        )

    def _select(self, dev: Device) -> None:
        self._selected_key = self._device_key(dev)
        self._render()
        self._on_select(dev)

    @staticmethod
    def _device_key(dev: Device) -> str:
        return dev.s_num or f"{dev.ip}:{dev.port}"
