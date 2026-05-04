from dsu.ui.flash_state import FlashState


def test_empty_state_has_no_active_flashes():
    s = FlashState()
    assert s.count == 0
    assert s.active_keys() == []
    assert s.is_flashing("dev1") is False


def test_start_marks_device_active():
    s = FlashState()
    s.start("dev1", total=1024)
    assert s.is_flashing("dev1") is True
    assert s.count == 1
    assert s.progress("dev1") == (0, 1024)


def test_update_changes_progress():
    s = FlashState()
    s.start("dev1", total=1000)
    s.update("dev1", current=250)
    assert s.progress("dev1") == (250, 1000)
    assert s.percent("dev1") == 25


def test_percent_returns_zero_for_unknown_device():
    s = FlashState()
    assert s.percent("nope") == 0


def test_finish_removes_device():
    s = FlashState()
    s.start("dev1", total=10)
    s.finish("dev1")
    assert s.is_flashing("dev1") is False
    assert s.count == 0


def test_listener_called_on_state_change():
    s = FlashState()
    calls = []
    s.subscribe(lambda: calls.append(1))
    s.start("dev1", total=10)
    s.update("dev1", current=5)
    s.finish("dev1")
    assert len(calls) == 3
