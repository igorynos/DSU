from dsu.domain.events import DevLstEvent, EventBus
from dsu.domain.models import Device
from dsu.domain.registry import DeviceRegistry


def _dev(serial="abc", ip="10.0.0.1", port=1775):
    d = Device.from_address(ip, port)
    d.s_num = serial
    return d


def test_empty_registry():
    bus = EventBus()
    reg = DeviceRegistry(bus)
    assert len(reg) == 0
    assert list(reg) == []


def test_add_emits_append():
    bus = EventBus()
    seen = []
    bus.bind(lambda e, dev=None, **_: seen.append((e, dev.s_num)),
             DevLstEvent.APPEND_DEV)
    reg = DeviceRegistry(bus)

    d = _dev("s1")
    reg.add(d)

    assert len(reg) == 1
    assert seen == [(DevLstEvent.APPEND_DEV, "s1")]


def test_add_existing_emits_poll_response():
    bus = EventBus()
    events = []
    bus.bind(lambda e, **_: events.append(e), [DevLstEvent.APPEND_DEV,
                                               DevLstEvent.POLL_RESPONSE])
    reg = DeviceRegistry(bus)

    reg.add(_dev("s1"))
    reg.add(_dev("s1"))

    assert events == [DevLstEvent.APPEND_DEV, DevLstEvent.POLL_RESPONSE]
    assert len(reg) == 1


def test_add_with_changed_fields_emits_update():
    bus = EventBus()
    events = []
    bus.bind(lambda e, **_: events.append(e), [DevLstEvent.APPEND_DEV,
                                               DevLstEvent.UPDATE_DEV,
                                               DevLstEvent.POLL_RESPONSE])
    reg = DeviceRegistry(bus)

    reg.add(_dev("s1", ip="10.0.0.1"))
    reg.add(_dev("s1", ip="10.0.0.2"))

    assert events[0] == DevLstEvent.APPEND_DEV
    assert DevLstEvent.UPDATE_DEV in events
    assert reg.find_by_serial("s1").ip == "10.0.0.2"


def test_remove_emits_remove():
    bus = EventBus()
    seen = []
    bus.bind(lambda e, **_: seen.append(e), DevLstEvent.REMOVE_DEV)
    reg = DeviceRegistry(bus)

    d = _dev("s1")
    reg.add(d)
    reg.remove(d)

    assert len(reg) == 0
    assert seen == [DevLstEvent.REMOVE_DEV]


def test_remove_unknown_is_noop():
    bus = EventBus()
    seen = []
    bus.bind(lambda e, **_: seen.append(e), DevLstEvent.REMOVE_DEV)
    reg = DeviceRegistry(bus)

    reg.remove(_dev("ghost"))

    assert seen == []


def test_find_by_serial():
    reg = DeviceRegistry(EventBus())
    reg.add(_dev("a"))
    reg.add(_dev("b"))
    assert reg.find_by_serial("b").s_num == "b"
    assert reg.find_by_serial("missing") is None


def test_find_by_address():
    reg = DeviceRegistry(EventBus())
    reg.add(Device.from_address("10.0.0.5", 1775))
    found = reg.find_by_address(("10.0.0.5", 1775))
    assert found is not None
    assert reg.find_by_address(("10.0.0.6", 1775)) is None


def test_iter_and_len():
    reg = DeviceRegistry(EventBus())
    reg.add(_dev("a"))
    reg.add(_dev("b"))
    serials = [d.s_num for d in reg]
    assert sorted(serials) == ["a", "b"]
    assert len(reg) == 2


def test_clear_removes_all_silently():
    bus = EventBus()
    seen = []
    bus.bind(lambda e, **_: seen.append(e), DevLstEvent.REMOVE_DEV)
    reg = DeviceRegistry(bus)
    reg.add(_dev("a"))
    reg.add(_dev("b"))
    seen.clear()

    reg.clear()

    assert len(reg) == 0
    # clear() is intentionally silent — no events fired.
    assert seen == []
