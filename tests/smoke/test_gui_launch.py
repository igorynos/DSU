"""Smoke test: GUI imports and constructs AppView without exceptions.

Set DSU_GUI_SMOKE=1 to enable. Headless CI: skip.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("DSU_GUI_SMOKE") != "1",
    reason="GUI smoke test requires DSU_GUI_SMOKE=1",
)


def test_app_view_constructs():
    """Building AppView with a fake Page should not raise."""
    from unittest.mock import MagicMock

    fake_page = MagicMock()
    fake_page.overlay = []

    from dsu.app import create_app
    from dsu.ui.app_view import AppView

    app = create_app()
    try:
        view = AppView(fake_page, app)
        assert view.control is not None
    finally:
        app.shutdown()


def test_run_function_exists():
    from dsu.ui import run
    assert callable(run)
