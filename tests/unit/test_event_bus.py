from dataclasses import dataclass
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.events.base import DomainEvent
from app.events.bus import EventBus


@dataclass
class SampleEvent(DomainEvent):
    payload: str


@dataclass
class OtherSampleEvent(DomainEvent):
    value: int


class SampleHandler:
    def __init__(self):
        self.handle = AsyncMock()


class OtherSampleHandler:
    def __init__(self):
        self.handle = AsyncMock()


@pytest.mark.asyncio
async def test_should_call_subscribed_handler():
    bus = EventBus()
    handler = SampleHandler()

    bus.subscribe(SampleEvent, handler)

    await bus.publish(
        SampleEvent(
            occurred_at=datetime.utcnow(),
            payload="hello",
        )
    )

    handler.handle.assert_awaited_once()


@pytest.mark.asyncio
async def test_should_not_duplicate_same_handler_class_for_event():
    bus = EventBus()
    handler = SampleHandler()

    bus.subscribe(SampleEvent, handler)
    bus.subscribe(SampleEvent, handler)

    await bus.publish(
        SampleEvent(
            occurred_at=datetime.utcnow(),
            payload="dup",
        )
    )

    handler.handle.assert_awaited_once()
    assert len(bus._handlers[SampleEvent]) == 1


@pytest.mark.asyncio
async def test_should_allow_multiple_handlers_for_same_event():
    bus = EventBus()
    handler_a = SampleHandler()
    handler_b = OtherSampleHandler()

    bus.subscribe(SampleEvent, handler_a)
    bus.subscribe(SampleEvent, handler_b)

    await bus.publish(
        SampleEvent(
            occurred_at=datetime.utcnow(),
            payload="fanout",
        )
    )

    handler_a.handle.assert_awaited_once()
    handler_b.handle.assert_awaited_once()


@pytest.mark.asyncio
async def test_should_allow_same_handler_class_for_different_events():
    bus = EventBus()
    handler_a = SampleHandler()
    handler_b = SampleHandler()

    bus.subscribe(SampleEvent, handler_a)
    bus.subscribe(OtherSampleEvent, handler_b)

    await bus.publish(
        SampleEvent(
            occurred_at=datetime.utcnow(),
            payload="a",
        )
    )
    await bus.publish(
        OtherSampleEvent(
            occurred_at=datetime.utcnow(),
            value=123,
        )
    )

    handler_a.handle.assert_awaited_once()
    handler_b.handle.assert_awaited_once()


@pytest.mark.asyncio
async def test_should_not_fail_when_no_handlers_registered():
    bus = EventBus()

    await bus.publish(
        SampleEvent(
            occurred_at=datetime.utcnow(),
            payload="noop",
        )
    )
