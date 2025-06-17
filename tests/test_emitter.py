import pytest
import asyncio
from src.archi.emitter import Emitter, EmitterFactory
from src.archi.broker import Broker

pytestmark = pytest.mark.asyncio

def test_emitter_uuid_generated():
    emitter = Emitter()
    assert isinstance(emitter.uuid, str)

def test_emitter_manual_uuid():
    emitter = Emitter(uuid="abc-123")
    assert emitter.uuid == "abc-123"

def test_factory_creates_emitter_with_uuid():
    emitter = EmitterFactory.create_emitter(uuid="factory-uuid")
    assert isinstance(emitter, Emitter)
    assert emitter.uuid == "factory-uuid"

def test_factory_creates_emitter_without_uuid():
    emitter = EmitterFactory.create_emitter()
    assert isinstance(emitter, Emitter)
    assert isinstance(emitter.uuid, str)

def test_factory_sets_resolve_callback():
    called = False
    def cb():
        nonlocal called
        called = True
    emitter = EmitterFactory.create_emitter(resolve_callback=cb)
    emitter._resolve()
    assert called

@pytest.mark.asyncio
async def test_emitter_without_broker():
    emitter = Emitter()
    with pytest.raises(RuntimeError, match="Emitter has no broker"):
        await emitter.emit()

@pytest.mark.asyncio
async def test_emitter_timeout_with_broker():
    broker = Broker(timeout=0.1)
    asyncio.create_task(broker.start_big_session())
    emitter = Emitter()
    broker.register_emitter(emitter)
    # Do not resolve emitter, should timeout
    result = await broker.collect_emit(emitter.uuid)
    assert result is False

@pytest.mark.asyncio
async def test_emitter_resolve_with_broker():
    broker = Broker(timeout=0.2)
    asyncio.create_task(broker.start_big_session())
    emitter = Emitter()
    broker.register_emitter(emitter)
    # Start session and resolve
    task = asyncio.create_task(broker.collect_emit(emitter.uuid))
    await asyncio.sleep(0.05)
    emitter._resolve()
    result = await task
    assert result is True