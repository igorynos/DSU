"""Top toolbar: logo, search field, theme toggle, hamburger button."""

from __future__ import annotations

from collections.abc import Callable

import flet as ft


def build_toolbar(
    *,
    on_search_change: Callable[[str], None],
    on_theme_toggle: Callable[[], None],
    on_menu_open: Callable[[ft.ControlEvent], None],
) -> ft.Container:
    search = ft.TextField(
        hint_text="Search devices…",
        prefix_icon=ft.Icons.SEARCH,
        height=36,
        text_size=12,
        content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
        expand=True,
        on_change=lambda e: on_search_change(e.control.value or ""),
    )

    theme_btn = ft.IconButton(
        icon=ft.Icons.DARK_MODE_OUTLINED,
        tooltip="Toggle theme",
        on_click=lambda _: on_theme_toggle(),
    )

    menu_btn = ft.IconButton(
        icon=ft.Icons.MENU,
        tooltip="Menu",
        on_click=on_menu_open,
    )

    return ft.Container(
        height=48,
        padding=ft.padding.symmetric(horizontal=12),
        content=ft.Row(
            controls=[
                ft.Text("⚡ DSU", weight=ft.FontWeight.BOLD, size=14),
                ft.Container(width=12),
                ft.Container(content=search, expand=True),
                theme_btn,
                menu_btn,
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
