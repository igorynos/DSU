"""Toast notifications (top-level snackbars) bound to a Flet page."""

from __future__ import annotations

from typing import Literal

import flet as ft

ToastKind = Literal["success", "error", "info"]

_BG = {
    "success": "#1d3a2a",
    "error":   "#3a1d1d",
    "info":    "#252525",
}
_FG = {
    "success": "#4ade80",
    "error":   "#ef4444",
    "info":    "#dddddd",
}


def show_toast(page: ft.Page, text: str, kind: ToastKind = "info") -> None:
    icon = {"success": "✓", "error": "✕", "info": "ⓘ"}[kind]
    page.snack_bar = ft.SnackBar(
        content=ft.Text(f"{icon}  {text}", color=_FG[kind]),
        bgcolor=_BG[kind],
        duration=4000,
        show_close_icon=True,
    )
    page.snack_bar.open = True
    page.update()
