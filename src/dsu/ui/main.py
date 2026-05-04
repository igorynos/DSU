"""Flet entry point — wires Application into a Flet page."""

from __future__ import annotations

import logging

import flet as ft

from dsu.app import Application, create_app
from dsu.ui.app_view import AppView

LOG = logging.getLogger("dsu.ui")


def run_app(page: ft.Page, app: Application) -> None:
    page.title = "DSU"
    page.theme_mode = ft.ThemeMode.SYSTEM
    # Flet 0.84: window size props live on page.window sub-object
    page.window.min_width = 1200
    page.window.min_height = 700
    page.padding = 0

    view = AppView(page, app)
    page.add(view.control)
    LOG.info("DSU GUI started")


def run() -> None:
    app = create_app()
    app.start()
    try:
        ft.app(target=lambda page: run_app(page, app))
    finally:
        app.shutdown()
