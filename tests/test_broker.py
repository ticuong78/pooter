import pytest
import asyncio
from unittest.mock import AsyncMock
from src.archi.broker import Broker, BrokerManager, BrokerFactory
from src.archi.emitter import Emitter
from src.archi.consumer import Consumer

@pytest.mark.asyncio
async def test_broker_single_session_and_emitters():
    broker = Broker(timeout=0.5)
    emitter1 = Emitter()
    emitter2 = Emitter()
    broker.register_emitter(emitter1)
    broker.register_emitter(emitter2)

    emitter1.resolve_callback = lambda: None
    emitter2.resolve_callback = lambda: None

    task = asyncio.create_task(emitter1.emit())
    await asyncio.sleep(0.01)
    emitter2._resolve()
    result = await task

    assert result is True

@pytest.mark.asyncio
async def test_broker_session_handles_timeout():
    broker = Broker(timeout=0.1)
    emitter1 = Emitter()
    emitter2 = Emitter()
    emitter1.resolve_callback = lambda: None

    broker.register_emitter(emitter1)
    broker.register_emitter(emitter2)

    result = await emitter1.emit()
    assert result is False

@pytest.mark.asyncio
async def test_broker_consumers_are_broadcasted():
    broker = Broker(timeout=0.3)
    emitter1 = Emitter()
    broker.register_emitter(emitter1)

    consumer = Consumer()
    triggered = False
    async def fake_consume():
        nonlocal triggered
        triggered = True

    consumer.consume = fake_consume
    broker.register_consumer(consumer)

    emitter1.resolve_callback = lambda: None
    await emitter1.emit()

    assert triggered

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

    emitter1.resolve_callback = lambda: None
    emitter2.resolve_callback = lambda: None

    broker.register_emitter(emitter1)
    broker.register_emitter(emitter2)

    async def resolve_later():
        await asyncio.sleep(0.01)
        emitter2._resolve()

    result = await asyncio.gather(
        emitter1.emit(),
        resolve_later()
    )

    assert result[0] is True

@pytest.mark.asyncio
async def test_collect_emit_with_timeout_and_unresolved_emitter():
    broker = Broker(timeout=0.2)
    emitter1 = Emitter("E1")
    emitter2 = Emitter("E2")

    emitter1.resolve_callback = lambda: None

    broker.register_emitter(emitter1)
    broker.register_emitter(emitter2)

    result = await emitter1.emit()
    assert result is False

@pytest.mark.asyncio
async def test_ignore_nonexistent_emitter():
    broker = Broker(timeout=0.1)
    await broker.collect_emit("NOT_FOUND")
    assert not broker._session_opened

@pytest.mark.asyncio
async def test_cannot_register_emitter_during_open_session(caplog):
    broker = Broker(timeout=5)
    emitter1 = Emitter("E1")
    emitter2 = Emitter("E2")
    emitter3 = Emitter("E3")

    broker.register_emitter(emitter1)
    broker.register_emitter(emitter2)

    started = asyncio.Event()

    async def trigger_emit():
        started.set()
        await emitter1.emit()
        await asyncio.sleep(2)
        await emitter2.emit()

    async def late_register():
        await started.wait()
        broker.register_emitter(emitter3)

    with caplog.at_level("WARNING"):
        await asyncio.gather(
            trigger_emit(),
            late_register()
        )

    # emitter2 đáng lý không được đăng ký
    assert emitter3.uuid not in broker.emitters

    # kiểm tra log cảnh báo
    assert any("Broker is opening a session" in record.message for record in caplog.records)

# -------- BrokerManager & Factory Tests --------

def test_create_broker_adds_to_manager():
    manager = BrokerManager()
    broker = manager.create_broker(timeout=1.5)
    assert broker.uuid in [b.uuid for b in manager.get_all_brokers()]
    assert broker.timeout == 1.5

def test_register_existing_broker():
    manager = BrokerManager()
    broker = BrokerFactory.create_broker()
    manager.register_broker(broker)
    assert manager.get_broker(broker.uuid) is broker

def test_register_duplicate_broker_raises():
    manager = BrokerManager()
    broker = BrokerFactory.create_broker(uuid="duplicate-id")
    manager.register_broker(broker)

    with pytest.raises(ValueError):
        manager.register_broker(broker)

def test_get_broker_returns_correct_instance():
    manager = BrokerManager()
    broker = manager.create_broker()
    assert manager.get_broker(broker.uuid) is broker

def test_remove_broker_success():
    manager = BrokerManager()
    broker = manager.create_broker()
    assert manager.remove_broker(broker.uuid) is True
    assert manager.get_broker(broker.uuid) is None

def test_remove_broker_failure():
    manager = BrokerManager()
    assert manager.remove_broker("not-found") is False

def test_register_emitter_to_valid_broker():
    manager = BrokerManager()
    broker = manager.create_broker()
    emitter = Emitter()
    manager.register_emitter_to(broker.uuid, emitter)
    assert emitter.uuid in broker.emitters
    assert emitter.broker is broker

def test_register_emitter_to_invalid_broker_raises():
    manager = BrokerManager()
    emitter = Emitter()
    with pytest.raises(ValueError):
        manager.register_emitter_to("invalid", emitter)

def test_update_broker_timeout():
    manager = BrokerManager()
    broker = manager.create_broker(timeout=1.0)
    manager.update_broker_timeout(broker.uuid, timeout=3.5)
    assert broker.timeout == 3.5

def test_get_all_brokers_returns_list():
    manager = BrokerManager()
    b1 = manager.create_broker()
    b2 = manager.create_broker()
    all_brokers = manager.get_all_brokers()
    assert b1 in all_brokers and b2 in all_brokers
