"""Flet entry point — wires Application into a Flet page."""

from __future__ import annotations

import flet as ft

from dsu.app import Application, create_app


def run_app(page: ft.Page, app: Application) -> None:
    page.title = "DSU"
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.window_min_width = 1200
    page.window_min_height = 700
    page.add(ft.Text("DSU GUI — Task 1 stub"))

    def _on_close(_):
        app.shutdown()

    page.on_close = _on_close


def run() -> None:
    app = create_app()
    app.start()
    ft.app(target=lambda page: run_app(page, app))
