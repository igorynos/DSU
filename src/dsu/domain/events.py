"""Event bus for the device registry (formerly the cbs machinery in DeviceList)."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from enum import Enum, auto

Handler = Callable[..., None]


class DevLstEvent(Enum):
    APPEND_DEV = auto()
    REMOVE_DEV = auto()
    UPDATE_DEV = auto()
    POLL_RESPONSE = auto()
    CMD_RESPONSE = auto()
    CON_FAIL = auto()


def _normalize_events(
    events: DevLstEvent | Iterable[DevLstEvent] | None,
) -> list[DevLstEvent]:
    if events is None:
        return list(DevLstEvent)
    if isinstance(events, DevLstEvent):
        return [events]
    return list(events)


def _normalize_handlers(
    handlers: Handler | Iterable[Handler] | None,
) -> list[Handler]:
    if handlers is None:
        return []
    if callable(handlers):
        return [handlers]
    return list(handlers)


class EventBus:
    def __init__(self) -> None:
        self._subs: dict[DevLstEvent, list[Handler]] = {e: [] for e in DevLstEvent}

    def bind(
        self,
        handlers: Handler | Iterable[Handler] | None = None,
        events: DevLstEvent | Iterable[DevLstEvent] | None = None,
    ) -> None:
        for event in _normalize_events(events):
            for handler in _normalize_handlers(handlers):
                if handler not in self._subs[event]:
                    self._subs[event].append(handler)

    def unbind(
        self,
        handlers: Handler | Iterable[Handler] | None = None,
        events: DevLstEvent | Iterable[DevLstEvent] | None = None,
    ) -> None:
        for event in _normalize_events(events):
            if handlers is None:
                self._subs[event].clear()
                continue
            for handler in _normalize_handlers(handlers):
                if handler in self._subs[event]:
                    self._subs[event].remove(handler)

    def emit(self, event: DevLstEvent, **payload) -> None:
        for handler in list(self._subs[event]):
            handler(event, **payload)
