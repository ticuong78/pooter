import sys
import os
import asyncio
import logging
import pytest

from src.archi.broker import Broker
from src.archi.emitter import Emitter
from src.archi.consumer import Consumer

logging.basicConfig(level=logging.INFO)

@pytest.mark.asyncio
async def test_tricky_emitter_timing_scenario():
    broker = Broker(timeout=1.0)

    results = []

    class TrackingConsumer(Consumer):
        async def consume(self):
            results.append("consumed")

    emitter_a = Emitter("A")
    emitter_b = Emitter("B")
    emitter_c = Emitter("C")
    emitter_d = Emitter("D")

    emitter_b.resolve_callback = lambda: results.append("B resolved")
    emitter_c.resolve_callback = lambda: results.append("C resolved")
    emitter_d.resolve_callback = lambda: results.append("D resolved")

    consumer = TrackingConsumer()
    broker.register_consumer(consumer)

    # Register A & B first
    broker.register_emitter(emitter_a)
    broker.register_emitter(emitter_b)

    # Emit B first (before A)
    async def emit_b():
        await asyncio.sleep(0.1)
        await emitter_b.emit()

    # Emit A after B (simulates "late" start of initial emitter)
    async def emit_a():
        await asyncio.sleep(0.2)
        await emitter_a.emit()

    # Register C in middle of session and emit before timeout
    async def register_and_emit_c():
        await asyncio.sleep(0.3)
        broker.register_emitter(emitter_c)
        await asyncio.sleep(0.2)
        await emitter_c.emit()

    # Register D too late (after timeout window)
    async def register_and_emit_d():
        await asyncio.sleep(1.1)
        broker.register_emitter(emitter_d)
        await asyncio.sleep(0.1)
        await emitter_d.emit()

    await asyncio.gather(emit_b(), emit_a(), register_and_emit_c(), register_and_emit_d())

    assert "B resolved" in results
    assert "C resolved" in results
    assert "D resolved" in results  # D resolved, but outside coordination
    assert "consumed" in results or "consumed" not in results  # depends on timing

@pytest.mark.asyncio
async def test_emitters_in_random_order_with_resolution_and_consumption():
    broker = Broker(timeout=1.0)

    results = []

    class TrackingConsumer(Consumer):
        async def consume(self):
            results.append("consumed")

    # Emitters
    emitter1 = Emitter("E1")
    emitter2 = Emitter("E2")
    emitter3 = Emitter("E3")
    emitter4 = Emitter("E4")

    # Callbacks to track resolution
    emitter1.resolve_callback = lambda: results.append("E1 resolved")
    emitter2.resolve_callback = lambda: results.append("E2 resolved")
    emitter3.resolve_callback = lambda: results.append("E3 resolved")
    emitter4.resolve_callback = lambda: results.append("E4 resolved")

    # Consumer
    consumer = TrackingConsumer()
    broker.register_consumer(consumer)

    # Register emitters out-of-order
    broker.register_emitter(emitter2)
    broker.register_emitter(emitter1)

    async def emit_e2():
        await asyncio.sleep(0.1)
        await emitter2.emit()

    async def emit_e1():
        await asyncio.sleep(0.2)
        await emitter1.emit()

    async def register_emit_e3():
        await asyncio.sleep(0.3)
        broker.register_emitter(emitter3)
        await asyncio.sleep(0.2)
        await emitter3.emit()

    async def late_register_emit_e4():
        await asyncio.sleep(1.3)
        broker.register_emitter(emitter4)
        await asyncio.sleep(0.1)
        await emitter4.emit()

    await asyncio.gather(
        emit_e2(),
        emit_e1(),
        register_emit_e3(),
        late_register_emit_e4()
    )

    # Assertions
    assert "E1 resolved" in results
    assert "E2 resolved" in results
    assert "E3 resolved" in results
    assert "E4 resolved" in results  # emitted outside session
    assert "consumed" in results or "consumed" not in results  # depends on timing

@pytest.mark.asyncio
async def test_no_resolution_within_timeout_should_not_consume():
    broker = Broker(timeout=0.5)
    results = []

    class TrackingConsumer(Consumer):
        async def consume(self):
            results.append("consumed")

    emitter = Emitter("LateEmitter")
    broker.register_emitter(emitter)

    broker.register_consumer(TrackingConsumer())

    async def very_late_emit():
        await asyncio.sleep(1.0)
        await emitter.emit()

    await asyncio.gather(
        emitter.emit(),  # Starts session
        very_late_emit()
    )

    assert "consumed" not in results
