"""Modal yes/no confirmation dialog."""

from __future__ import annotations

from collections.abc import Callable

import flet as ft


def show_confirm(
    page: ft.Page,
    text: str,
    *,
    confirm_label: str = "Confirm",
    on_yes: Callable[[], None],
) -> None:
    def close(_):
        page.dialog.open = False
        page.update()

    def yes(_):
        close(_)
        on_yes()

    page.dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Are you sure?"),
        content=ft.Text(text),
        actions=[
            ft.TextButton("Cancel", on_click=close),
            ft.FilledButton(confirm_label, on_click=yes,
                            style=ft.ButtonStyle(bgcolor="#dc2626")),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.dialog.open = True
    page.update()
