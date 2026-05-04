"""Console-script entry point."""

from __future__ import annotations

import argparse
import logging
import signal
import time

from dsu.app import create_app
from dsu.domain.events import DevLstEvent

LOG = logging.getLogger("dsu")


def _log_event(event: DevLstEvent, **payload):
    dev = payload.get("dev")
    if dev is None:
        LOG.info("%s", event.name)
    else:
        LOG.info("%s %s", event.name, dev)


def main() -> int:
    parser = argparse.ArgumentParser(prog="dsu", description="Device Setup Utility")
    parser.add_argument("--debug", action="store_true",
                        help="Enable verbose logging and (if installed) keyboard hotkeys.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    with create_app() as app:
        for event in DevLstEvent:
            app.events.bind(_log_event, event)

        if args.debug:
            try:
                from dsu.hotkeys import register_debug_hotkeys
                register_debug_hotkeys(app)
            except ImportError as e:
                LOG.warning("hotkeys disabled: %s", e)

        stop = False
        def _on_signal(*_):
            nonlocal stop
            stop = True

        signal.signal(signal.SIGINT, _on_signal)
        signal.signal(signal.SIGTERM, _on_signal)

        LOG.info("DSU started. Press Ctrl+C to exit.")
        while not stop:
            time.sleep(0.5)

    return 0
