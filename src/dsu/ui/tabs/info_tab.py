"""Read-only Info tab content."""

from __future__ import annotations

import flet as ft

from dsu.domain.models import Device


def build_info_tab(dev: Device) -> ft.Control:
    rows = [
        ("Serial",     dev.s_num or "—"),
        ("MAC",        dev.mac or "—"),
        ("Boot mode",  dev.boot_mode or "—"),
        ("FW",         dev.fw or "—"),
        ("Bootloader", dev.btldr or "—"),
        ("PCB",        dev.pcb or "—"),
        ("Comment",    dev.comment or "—"),
    ]

    cells = []
    for label, value in rows:
        cells.append(
            ft.Row(controls=[
                ft.Text(f"{label}:", size=11, color="#888"),
                ft.Text(value, size=11, selectable=True),
            ], spacing=6),
        )

    grid = ft.Column(
        controls=[
            ft.Row(controls=cells[0:3], spacing=24),
            ft.Row(controls=cells[3:6], spacing=24),
            ft.Row(controls=cells[6:7], spacing=24),
        ],
        spacing=10,
    )
    return ft.Container(padding=ft.padding.all(12), content=grid)
