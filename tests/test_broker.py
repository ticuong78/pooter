import pytest
import asyncio
from src.archi.broker import Broker
from src.archi.emitter import Emitter
from src.archi.consumer import Consumer
from src.archi.event import EventBus

pytestmark = pytest.mark.asyncio

@pytest.mark.asyncio
async def test_emit_and_resolve_consumes():
    broker = Broker()
    emitter1 = Emitter()
    emitter2 = Emitter()
    consumer = Consumer()

    triggered = False

    async def fake_consume():
        nonlocal triggered
        triggered = True

    consumer.consume = fake_consume

    broker.register_emitter(emitter1)
    broker.register_emitter(emitter2)
    broker.register_consumer(consumer)

    # Start first emit
    emit_task1 = asyncio.create_task(emitter1.emit())
    await asyncio.sleep(0.1)  # Give time for section to open
    
    # Start second emit
    emit_task2 = asyncio.create_task(emitter2.emit())
    
    # Wait for both to complete
    await asyncio.gather(emit_task1, emit_task2)
    
    assert triggered
    assert not broker.opened_section  # Section should be closed after all emitters complete

@pytest.mark.asyncio
async def test_broker_registration():
    broker = Broker()
    emitter = Emitter()
    consumer = Consumer()
    
    broker.register_emitter(emitter)
    broker.register_consumer(consumer)
    
    assert emitter.uuid in broker.emitters
    assert consumer.uuid in broker.consumers
    assert emitter.broker == broker

@pytest.mark.asyncio
async def test_broker_timeout():
    broker = Broker(timeout=0.1)
    emitter = Emitter()
    consumer = Consumer()
    
    broker.register_emitter(emitter)
    broker.register_consumer(consumer)
    
    # Start emit but don't resolve
    emit_task = asyncio.create_task(emitter.emit())
    
    # Wait for timeout
    await asyncio.sleep(0.2)
    
    # State should be cleared after timeout
    assert not broker.emitted
    assert not broker.opened_section

@pytest.mark.asyncio
async def test_broker_section_management():
    broker = Broker()
    emitter = Emitter()
    emitter2 = Emitter()
    
    broker.register_emitter(emitter)
    broker.register_emitter(emitter2)
    
    # Start emit
    emit_task = asyncio.create_task(emitter.emit())
    await asyncio.sleep(0.1)

    # Should be in section
    assert broker.opened_section

    emit_task2 = asyncio.create_task(emitter2.emit())

    await asyncio.gather(emit_task, emit_task2)

@pytest.mark.asyncio
async def test_broker_multiple_emitters():
    broker = Broker()
    emitters = [Emitter() for _ in range(3)]
    consumer = Consumer()
    
    consume_count = 0
    async def count_consume():
        nonlocal consume_count
        consume_count += 1
    
    consumer.consume = count_consume
    
    for emitter in emitters:
        broker.register_emitter(emitter)
    broker.register_consumer(consumer)
    
    # Start all emits
    emit_tasks = [asyncio.create_task(e.emit()) for e in emitters]
    
    # Wait for all emits to complete
    await asyncio.gather(*emit_tasks)
    
    # Consumer should be called once
    assert consume_count == 1
    # Section should be closed
    assert not broker.opened_section

@pytest.mark.asyncio
async def test_broker_registers_multiple_emitters():
    broker = Broker()
    emitter1 = Emitter()
    emitter2 = Emitter()
    broker.register_emitter(emitter1)
    broker.register_emitter(emitter2)
    assert emitter1.uuid in broker.emitters
    assert emitter2.uuid in broker.emitters
    assert emitter1.broker == broker
    assert emitter2.broker == broker

@pytest.mark.asyncio
async def test_broker_consumes_with_multiple_emitters():
    broker = Broker()
    emitter1 = Emitter()
    emitter2 = Emitter()
    consumer = Consumer()
    triggered = False
    async def fake_consume():
        nonlocal triggered
        triggered = True
    consumer.consume = fake_consume
    broker.register_emitter(emitter1)
    broker.register_emitter(emitter2)
    broker.register_consumer(consumer)
    emit_task1 = asyncio.create_task(emitter1.emit())
    await asyncio.sleep(0.1)
    emit_task2 = asyncio.create_task(emitter2.emit())
    await asyncio.gather(emit_task1, emit_task2)
    assert triggered
    assert not broker.opened_section

@pytest.mark.asyncio
async def test_broker_section_state_with_multiple_emitters():
    broker = Broker()
    emitter1 = Emitter()
    emitter2 = Emitter()
    broker.register_emitter(emitter1)
    broker.register_emitter(emitter2)
    emit_task1 = asyncio.create_task(emitter1.emit())
    await asyncio.sleep(0.1)
    assert broker.opened_section
    emit_task2 = asyncio.create_task(emitter2.emit())
    await asyncio.gather(emit_task1, emit_task2)
    assert not broker.opened_section

@pytest.mark.asyncio
async def test_broker_timeout_with_multiple_emitters():
    broker = Broker(timeout=0.1)
    emitter1 = Emitter()
    emitter2 = Emitter()
    broker.register_emitter(emitter1)
    broker.register_emitter(emitter2)
    emit_task = asyncio.create_task(emitter1.emit())
    await asyncio.sleep(0.2)
    assert not broker.opened_section
    assert not broker.emitted

@pytest.mark.asyncio
async def test_collect_emit_returns_true_on_success():
    broker = Broker()
    emitter1 = Emitter()
    emitter2 = Emitter()
    broker.register_emitter(emitter1)
    broker.register_emitter(emitter2)

    # Start collect_emit for emitter1
    collect_task = asyncio.create_task(broker.collect_emit(emitter1.uuid))
    await asyncio.sleep(0.05)
    # Resolve emitter2 to allow collect_emit to finish
    emitter2._resolve()
    result = await collect_task

    assert result is True
    assert not broker.opened_section
    assert not broker.emitted

@pytest.mark.asyncio
async def test_collect_emit_returns_false_on_timeout():
    broker = Broker(timeout=0.1)
    emitter1 = Emitter()
    emitter2 = Emitter()
    broker.register_emitter(emitter1)
    broker.register_emitter(emitter2)

    # Only resolve one emitter, so the other will timeout
    result = await broker.collect_emit(emitter1.uuid)
    assert result is False
    assert not broker.opened_section
    assert not broker.emitted