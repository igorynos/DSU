"""Shared pytest fixtures."""

import pytest

from dsu.domain.events import EventBus
from dsu.domain.registry import DeviceRegistry


@pytest.fixture
def events():
    return EventBus()


@pytest.fixture
def registry(events):
    return DeviceRegistry(events)
