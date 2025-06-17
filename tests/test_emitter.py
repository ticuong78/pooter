import pytest
import asyncio
from src.archi.emitter import Emitter, EmitterFactory
from src.archi.broker import Broker
from unittest.mock import AsyncMock, MagicMock

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
    emitter = Emitter()
    broker.register_emitter(emitter)
    # Không resolve emitter, sẽ timeout
    result = await emitter.emit()
    assert result is True

@pytest.mark.asyncio
async def test_emitter_resolve_with_broker():
    broker = Broker(timeout=0.2)
    emitter = Emitter()
    broker.register_emitter(emitter)
    # Bắt đầu session và resolve
    task = asyncio.create_task(emitter.emit())
    await asyncio.sleep(0.05)
    emitter._resolve()
    result = await task
    assert result is True

@pytest.mark.asyncio
async def test_emit_starts_session_if_no_session_opened():
    emitter = Emitter("TEST-UUID")

    # Fake broker with no session opened
    broker = MagicMock()
    broker._session_opened = False
    broker.collect_emit = AsyncMock(return_value="session_started")

    emitter.broker = broker
    result = await emitter.emit()

    broker.collect_emit.assert_awaited_once_with("TEST-UUID")
    assert result == "session_started"


@pytest.mark.asyncio
async def test_emit_resolves_if_session_already_opened():
    emitter = Emitter("SECOND")

    broker = MagicMock()
    broker._session_opened = True

    emitter.broker = broker

    was_resolved = False
    def resolve_callback():
        nonlocal was_resolved
        was_resolved = True

    emitter.resolve_callback = resolve_callback

    result = await emitter.emit()

    assert was_resolved is True
    assert result is True


@pytest.mark.asyncio
async def test_emit_raises_if_no_broker():
    emitter = Emitter("NO-BROKER")
    with pytest.raises(RuntimeError, match="Emitter has no broker."):
        await emitter.emit()

@pytest.mark.asyncio
async def test_await_resolution_timeout():
    emitter = Emitter("TIMEOUT")

    with pytest.raises(TimeoutError, match="Emitter TIMEOUT timed out"):
        await emitter.await_resolution(timeout=0.1)


@pytest.mark.asyncio
async def test_resolve_sets_event_and_calls_callback():
    emitter = Emitter("RESOLVE-CHECK")

    was_called = False
    def callback():
        nonlocal was_called
        was_called = True

    emitter.resolve_callback = callback
    emitter._resolve()

    assert was_called is True
    assert emitter._resolved.is_set()
