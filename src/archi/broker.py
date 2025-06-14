# pyright: reportArgumentType=false

import asyncio
import logging
from typing import Callable, Awaitable, Optional

from _stub.consumer import Consumer
from _stub.emitter import Emitter

logger = logging.getLogger(__name__)

class Broker:
    def __init__(self, timeout_ms: int = 500):
        self._timeout_ms = timeout_ms / 1000  # convert to seconds
        self._emitters: dict[str, Emitter] = {}
        self._emitted: set[str] = set()
        self._consumers: dict[str, Consumer] = {}

        logger.info("[Broker] Initialized broker")

    def register_emitter(self, emitter: Emitter | list[Emitter]):
        emitters = emitter if isinstance(emitter, list) else [emitter]
        for e in emitters:
            self._emitters[e.uuid] = e
            e.register(self)

    def register_consumer(self, consumer: Consumer | list[Consumer]):
        consumers = consumer if isinstance(consumer, list) else [consumer]
        for c in consumers:
            self._consumers[c.uuid] = c
            c.register(self)

    async def collect_emit(self, uuid: str):
        if uuid not in self._emitters:
            logger.warning(f"[Broker] Unknown emitter UUID: {uuid}")
            return

        self._emitted.add(uuid)
        pending_emitters = [emitter for emitter in self._emitters.values() if emitter.uuid not in self._emitted]

        try:
            await asyncio.gather(*(self._wait_for_emitter(emitter) for emitter in pending_emitters))
            await self._announce()
        except Exception as e:
            self._emitted.clear()
            logger.error(f"[Broker] Coordination failed for {uuid}: {e}")

    async def _wait_for_emitter(self, emitter: Emitter):
        if emitter.uuid not in self._emitters:
            raise ValueError(f"Emitter {emitter.uuid} not registered.")

        future = asyncio.Future()

        def external_resolve():
            self._emitted.add(emitter.uuid)
            if not future.done():
                future.set_result(True)

        emitter.external_resolve = external_resolve

        try:
            await asyncio.wait_for(future, timeout=self._timeout_ms)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Timeout waiting for emitter {emitter.uuid}")

    async def _announce(self):
        try:
            await asyncio.gather(*(c.consume() for c in self._consumers.values()))
            logger.info(f"[Broker] Announced to {len(self._consumers)} consumers.")
        except Exception as e:
            logger.error(f"[Broker] Error occurred during announce: {e}")
