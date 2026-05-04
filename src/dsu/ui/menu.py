"""Hamburger popup menu — Refresh / Settings / About / Log / Test ▸ / Exit."""

from __future__ import annotations

from collections.abc import Callable

import flet as ft


def build_menu(
    *,
    on_refresh: Callable[[], None],
    on_settings: Callable[[], None],
    on_about: Callable[[], None],
    on_toggle_log: Callable[[], None],
    on_add_test_devices: Callable[[int], None],
    on_exit: Callable[[], None],
) -> ft.PopupMenuButton:
    test_submenu = ft.PopupMenuItem(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.SCIENCE_OUTLINED, size=16),
                ft.Text("Test"),
                ft.Icon(ft.Icons.ARROW_RIGHT, size=16),
            ],
        ),
    )

    return ft.PopupMenuButton(
        icon=ft.Icons.MORE_VERT,
        tooltip="Menu",
        items=[
            ft.PopupMenuItem(text="Refresh",  icon=ft.Icons.REFRESH,
                             on_click=lambda _: on_refresh()),
            ft.PopupMenuItem(text="Settings…", icon=ft.Icons.SETTINGS_OUTLINED,
                             on_click=lambda _: on_settings()),
            ft.PopupMenuItem(text="About",    icon=ft.Icons.INFO_OUTLINE,
                             on_click=lambda _: on_about()),
            ft.PopupMenuItem(),  # divider
            ft.PopupMenuItem(text="Show log panel", icon=ft.Icons.RECEIPT_LONG,
                             on_click=lambda _: on_toggle_log()),
            ft.PopupMenuItem(),  # divider
            ft.PopupMenuItem(text="Add 1 test device",
                             on_click=lambda _: on_add_test_devices(1)),
            ft.PopupMenuItem(text="Add 5 test devices",
                             on_click=lambda _: on_add_test_devices(5)),
            ft.PopupMenuItem(text="Add 10 test devices",
                             on_click=lambda _: on_add_test_devices(10)),
            ft.PopupMenuItem(),  # divider
            ft.PopupMenuItem(text="Exit", icon=ft.Icons.LOGOUT,
                             on_click=lambda _: on_exit()),
        ],
    )
