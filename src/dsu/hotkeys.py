"""Optional debug hotkeys. Requires the `keyboard` extra: pip install dsu[hotkeys]."""

from __future__ import annotations

import logging

LOG = logging.getLogger(__name__)


def register_debug_hotkeys(app) -> None:
    """Register F11 to dump the registry contents.

    Raises ImportError if the keyboard module is not installed.
    """
    import keyboard  # noqa: F401 — verifies the optional dep is present

    def dump_registry():
        for dev in app.registry:
            LOG.info("%s", dev)

    keyboard.add_hotkey("F11", dump_registry)
    LOG.info("debug hotkeys registered: F11=dump registry")
