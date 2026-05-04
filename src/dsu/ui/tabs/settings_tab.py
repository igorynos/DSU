"""Editable Settings tab — Apply/Reset buttons. Wired in main."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import flet as ft

from dsu.domain.models import Device


@dataclass
class SettingsForm:
    name: ft.TextField
    ip: ft.TextField
    mask: ft.TextField
    gateway: ft.TextField
    host: ft.TextField
    port: ft.TextField
    comment: ft.TextField

    def values(self) -> dict[str, object]:
        return {
            "name": self.name.value or "",
            "ip": self.ip.value or "",
            "mask": self.mask.value or "",
            "gateway": self.gateway.value or "",
            "host": self.host.value or "",
            "port": int(self.port.value or "0"),
            "comment": self.comment.value or "",
        }


def build_settings_tab(
    dev: Device,
    *,
    on_apply: Callable[[SettingsForm], None],
) -> ft.Control:
    def field(label: str, value: str, width: int = 220) -> ft.TextField:
        return ft.TextField(
            label=label, value=value, width=width,
            text_size=12, dense=True,
        )

    form = SettingsForm(
        name     = field("Name", dev.name or ""),
        ip       = field("IP", dev.ip or ""),
        mask     = field("Mask", dev.mask or ""),
        gateway  = field("Gateway", dev.gateway or ""),
        host     = field("Host", dev.host or ""),
        port     = field("Port", str(dev.port or 0), width=120),
        comment  = field("Comment", dev.comment or "", width=460),
    )

    apply_btn = ft.FilledButton("Apply", icon=ft.Icons.CHECK,
                                on_click=lambda _: on_apply(form))
    reset_btn = ft.OutlinedButton("Reset", icon=ft.Icons.UNDO,
                                  on_click=lambda _: _reset(form, dev))

    return ft.Container(
        padding=ft.padding.all(12),
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Row(controls=[form.name, form.port], spacing=12),
                ft.Row(controls=[form.ip, form.mask, form.gateway], spacing=12),
                ft.Row(controls=[form.host], spacing=12),
                ft.Row(controls=[form.comment], spacing=12),
                ft.Row(controls=[apply_btn, reset_btn], spacing=8),
            ],
        ),
    )


def _reset(form: SettingsForm, dev: Device) -> None:
    form.name.value = dev.name or ""
    form.ip.value = dev.ip or ""
    form.mask.value = dev.mask or ""
    form.gateway.value = dev.gateway or ""
    form.host.value = dev.host or ""
    form.port.value = str(dev.port or 0)
    form.comment.value = dev.comment or ""
    if form.name.page is not None:
        form.name.update()
        form.ip.update()
        form.mask.update()
        form.gateway.update()
        form.host.update()
        form.port.update()
        form.comment.update()
