import pytest
import asyncio
from src.archi.event import EventBus

pytestmark = pytest.mark.asyncio

@pytest.mark.asyncio
async def test_eventbus_async_handler():
    flag = False
    async def handler():
        nonlocal flag
        flag = True
    bus = EventBus()
    bus.subscribe("go", handler) # type: ignore
    await bus.emit("go")
    assert flag

@pytest.mark.asyncio
async def test_eventbus_sync_handler():
    flag = False
    def handler():
        nonlocal flag
        flag = True
    bus = EventBus()
    bus.subscribe("sync", handler)
    await bus.emit("sync")
    assert flag