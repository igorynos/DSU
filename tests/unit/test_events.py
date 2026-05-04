from dsu.domain.events import DevLstEvent, EventBus


def test_event_enum_members():
    assert {e.name for e in DevLstEvent} == {
        "APPEND_DEV", "REMOVE_DEV", "UPDATE_DEV",
        "POLL_RESPONSE", "CMD_RESPONSE", "CON_FAIL",
    }


def test_bind_and_emit_calls_handler():
    bus = EventBus()
    received = []

    def handler(event, payload=None):
        received.append((event, payload))

    bus.bind(handler, DevLstEvent.APPEND_DEV)
    bus.emit(DevLstEvent.APPEND_DEV, payload="x")

    assert received == [(DevLstEvent.APPEND_DEV, "x")]


def test_bind_to_multiple_events():
    bus = EventBus()
    seen = []
    bus.bind(lambda e, **_: seen.append(e),
             [DevLstEvent.APPEND_DEV, DevLstEvent.REMOVE_DEV])
    bus.emit(DevLstEvent.APPEND_DEV)
    bus.emit(DevLstEvent.UPDATE_DEV)
    bus.emit(DevLstEvent.REMOVE_DEV)
    assert seen == [DevLstEvent.APPEND_DEV, DevLstEvent.REMOVE_DEV]


def test_unbind_specific_handler():
    bus = EventBus()
    calls = []
    h1 = lambda e, **_: calls.append("h1")
    h2 = lambda e, **_: calls.append("h2")
    bus.bind([h1, h2], DevLstEvent.APPEND_DEV)
    bus.unbind(h1, DevLstEvent.APPEND_DEV)
    bus.emit(DevLstEvent.APPEND_DEV)
    assert calls == ["h2"]


def test_unbind_all_handlers_for_event():
    bus = EventBus()
    calls = []
    bus.bind(lambda e, **_: calls.append("x"), DevLstEvent.APPEND_DEV)
    bus.unbind(events=DevLstEvent.APPEND_DEV)
    bus.emit(DevLstEvent.APPEND_DEV)
    assert calls == []


def test_emit_with_kwargs():
    bus = EventBus()
    captured = {}
    bus.bind(lambda e, **kw: captured.update(kw), DevLstEvent.CMD_RESPONSE)
    bus.emit(DevLstEvent.CMD_RESPONSE, cmd="X", pack=b"\x01")
    assert captured == {"cmd": "X", "pack": b"\x01"}
