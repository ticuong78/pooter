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
async def test_emitter_in_section():
    emitter = Emitter()
    broker = Broker()
    broker.register_emitter(emitter)
    broker.opened_section = True
    await emitter.emit()
    assert emitter._resolved.is_set()

@pytest.mark.asyncio
async def test_emitter_timeout():
    broker = Broker(timeout=0.1)
    emitter1 = Emitter()
    emitter2 = Emitter()
    broker.register_emitter(emitter1)
    broker.register_emitter(emitter2)
    # Only start one emitter, so the other never resolves
    emit_task = asyncio.create_task(emitter1.emit())
    await asyncio.sleep(0.2)
    assert not emitter1._resolved.is_set()