"""Firmware tab — file picker, Flash button, progress bar."""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from dsu.domain.models import Device


class FirmwareTabState:
    """Mutable state shared between widget builds and the controller."""

    def __init__(self) -> None:
        self.path: str | None = None


def build_firmware_tab(
    dev: Device,
    *,
    state: FirmwareTabState,
    is_flashing: bool,
    progress_value: float,
    progress_text: str,
    on_pick_file: Callable[[], None],
    on_flash: Callable[[str], None],
) -> ft.Control:
    file_label = ft.Text(state.path or "No file selected",
                         size=11, color="#888")
    pick_btn = ft.OutlinedButton("Choose .bin / .fw\u2026",
                                 icon=ft.Icons.FOLDER_OPEN,
                                 on_click=lambda _: on_pick_file())

    flash_disabled = is_flashing or not state.path
    flash_btn = ft.FilledButton(
        "Flash",
        icon=ft.Icons.UPLOAD,
        disabled=flash_disabled,
        on_click=lambda _: on_flash(state.path) if state.path else None,
    )

    progress = ft.Column(
        controls=[
            ft.ProgressBar(value=progress_value, height=6),
            ft.Text(progress_text, size=11, color="#888"),
        ],
        spacing=4,
    ) if is_flashing else ft.Container()

    return ft.Container(
        padding=ft.padding.all(12),
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Row(controls=[pick_btn, file_label], spacing=12),
                ft.Row(controls=[flash_btn], spacing=8),
                progress,
            ],
        ),
    )
