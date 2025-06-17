import pytest
import asyncio
from src.archi.broker import Broker
from src.archi.emitter import Emitter
from src.archi.consumer import Consumer
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_broker_single_session_and_emitters():
    broker = Broker(timeout=0.2)
    emitter1 = Emitter()
    emitter2 = Emitter()
    broker.register_emitter(emitter1)
    broker.register_emitter(emitter2)
    # Start session and resolve both
    task = asyncio.create_task(emitter1.emit())
    await asyncio.sleep(0.05)
    emitter1._resolve()
    emitter2._resolve()
    result = await task
    assert result is True

@pytest.mark.asyncio
async def test_broker_session_handles_timeout():
    broker = Broker(timeout=0.1)
    emitter1 = Emitter()
    emitter2 = Emitter()
    broker.register_emitter(emitter1)
    broker.register_emitter(emitter2)
    # Do not resolve emitter1, should timeout
    result = await emitter1.emit()
    assert result is False

@pytest.mark.asyncio
async def test_broker_consumers_are_broadcasted():
    broker = Broker(timeout=0.2)
    emitter1 = Emitter()
    broker.register_emitter(emitter1)
    consumer = Consumer()
    triggered = False
    async def fake_consume():
        nonlocal triggered
        triggered = True
    consumer.consume = fake_consume
    broker.register_consumer(consumer)
    # Start session
    task = asyncio.create_task(emitter1.emit())
    await asyncio.sleep(0.05)
    emitter1._resolve()
    await task
    assert triggered

# ------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_emitter_and_consumer():
    broker = Broker(timeout=0.5)

    emitter = Emitter("E1")
    consumer = Consumer()
    consumer.consume = AsyncMock()

    broker.register_emitter(emitter)
    broker.register_consumer(consumer)

    assert emitter.uuid in broker.emitters
    assert consumer.uuid in broker.consumers
    assert consumer.consume in broker.event_bus._subscribers["all_resolved"]


@pytest.mark.asyncio
async def test_collect_emit_with_all_emitters_resolved():
    broker = Broker(timeout=0.3)

    emitter1 = Emitter("E1")
    emitter2 = Emitter("E2")

    # Callbacks that immediately resolve
    emitter1.resolve_callback = lambda: None
    emitter2.resolve_callback = lambda: None

    broker.register_emitter(emitter1)
    broker.register_emitter(emitter2)

    async def delayed_resolve():
        await asyncio.sleep(0.05)
        emitter2._resolve()

    # Start coordination
    result = await asyncio.gather(
        emitter1.emit(),
        delayed_resolve()
    )

    assert result[0] is True


@pytest.mark.asyncio
async def test_collect_emit_with_timeout_and_unresolved_emitter():
    broker = Broker(timeout=0.3)

    emitter1 = Emitter("E1")
    emitter2 = Emitter("E2")

    emitter1.resolve_callback = lambda: None
    # emitter2 intentionally does not resolve

    broker.register_emitter(emitter1)
    broker.register_emitter(emitter2)

    # Start coordination from emitter1
    result = await emitter1.emit()

    assert result is False


@pytest.mark.asyncio
async def test_late_registered_emitter_during_session():
    broker = Broker(timeout=0.4)

    emitter1 = Emitter("E1")
    emitter2 = Emitter("E2")

    emitter1.resolve_callback = lambda: None
    emitter2.resolve_callback = lambda: None

    broker.register_emitter(emitter1)

    async def late_register_and_emit():
        await asyncio.sleep(0.05)
        broker.register_emitter(emitter2)
        await asyncio.sleep(1.0)  # sau timeout của session
        await emitter2.emit()

    result = await asyncio.gather(
        emitter1.emit(),
        late_register_and_emit()
    )

    assert result[0] is False


@pytest.mark.asyncio
async def test_ignore_nonexistent_emitter():
    broker = Broker(timeout=0.1)

    # Emit bằng UUID chưa đăng ký → không lỗi
    await broker.collect_emit("NOT_FOUND")

    assert not broker._session_opened