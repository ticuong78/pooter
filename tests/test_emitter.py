import pytest
import asyncio
from src.archi.emitter import Emitter
from src.archi.broker import Broker

pytestmark = pytest.mark.asyncio

def test_emitter_uuid_generated():
    emitter = Emitter()
    assert isinstance(emitter.uuid, str)

def test_emitter_manual_uuid():
    emitter = Emitter(uuid="abc-123")
    assert emitter.uuid == "abc-123"

@pytest.mark.asyncio
async def test_emitter_without_broker():
    emitter = Emitter()
    with pytest.raises(RuntimeError, match="Emitter has no broker"):
        await emitter.emit()

@pytest.mark.asyncio
async def test_emitter_timeout():
    broker = Broker(timeout=0.1)
    emitter = Emitter()
    broker.register_emitter(emitter)
    
    # Create another emitter that won't resolve
    other_emitter = Emitter()
    broker.register_emitter(other_emitter)
    
    # Start emit
    emit_task = asyncio.create_task(emitter.emit())
    
    # Wait for timeout
    await asyncio.sleep(0.2)
    
    # Should have timed out
    assert not emitter._resolved.is_set()

@pytest.mark.asyncio
async def test_emitter_in_section():
    emitter = Emitter()
    broker = Broker()
    broker.register_emitter(emitter)
    
    # Set broker in section mode
    broker.opened_section = True
    
    # Emit should resolve immediately when in section
    await emitter.emit()
    assert emitter._resolved.is_set()