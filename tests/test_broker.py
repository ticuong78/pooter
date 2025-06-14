import pytest
import asyncio
from src.archi.broker import Broker
from src.archi.emitter import Emitter
from src.archi.consumer import Consumer

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

    emit_task = asyncio.create_task(emitter1.emit())
    await asyncio.sleep(0.1)
    emitter2.resolve()
    await emit_task

    assert triggered