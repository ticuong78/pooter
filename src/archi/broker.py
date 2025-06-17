import asyncio
import logging
from typing import Optional, Callable

from .emitter import Emitter, EmitterFactory
from .consumer import Consumer
from .event import EventBus

logger = logging.getLogger(__name__)

class Broker:
    def __init__(self, timeout: float = 1.0, event_bus: Optional[EventBus] = None, emitter_factory: Optional[EmitterFactory] = None):
        self.timeout = timeout
        self.emitters: dict[str, Emitter] = {}
        self.emitted: set[str] = set()
        self.consumers: dict[str, Consumer] = {}
        self.event_bus = event_bus or EventBus()
        self.emitter_factory = emitter_factory or EmitterFactory()

        self._emitter_tasks: dict[str, asyncio.Task] = {}
        self._session_opened = False
        self._session_lock = asyncio.Lock()

    def create_emitter(self, uuid: Optional[str] = None, resolve_callback: Optional[Callable[[], None]] = None) -> Emitter:
        emitter = self.emitter_factory.create_emitter(uuid, resolve_callback)
        self.register_emitter(emitter)
        return emitter

    def register_emitter(self, emitter: Emitter):
        self.emitters[emitter.uuid] = emitter
        emitter.broker = self  # type: ignore

        if self._session_opened:
            logger.info(f"[Broker] Emitter {emitter.uuid} registered during session.")
            task = asyncio.create_task(self._wait_and_collect(emitter))
            self._emitter_tasks[emitter.uuid] = task

    def unregister_emitter(self, emitter: Emitter):
        self.emitters.pop(emitter.uuid)

    def get_emitter(self, uuid: str) -> Emitter | None:
        return self.emitters[uuid]

    def get_all_emitters(self) -> list[Emitter]:
        return list(self.emitters.values())

    def register_consumer(self, consumer: Consumer):
        self.consumers[consumer.uuid] = consumer
        self.event_bus.subscribe("all_resolved", consumer.consume)  # type: ignore

    async def _wait_and_collect(self, emitter: Emitter):
        try:
            await emitter.await_resolution(timeout=self.timeout)
            self.emitted.add(emitter.uuid)
        except Exception as e:
            logger.error(f"[Broker] Error awaiting emitter {emitter.uuid}: {e}")

    async def collect_emit(self, uuid: str):
        if self.emitters.get(uuid) is None:
            logger.warning(f"[Broker] Ignoring emitter {uuid} — no longer part of coordination.")
            return False

        async with self._session_lock:
            logger.info(f"[Broker] Starting coordination session. First emitter: {uuid}")
            self._session_opened = True
            self.emitted.add(uuid)

            # Track all current emitters at session start
            for e_uuid, emitter in self.emitters.items():
                if e_uuid not in self.emitted and e_uuid not in self._emitter_tasks:
                    task = asyncio.create_task(self._wait_and_collect(emitter))
                    self._emitter_tasks[e_uuid] = task

            # Wait for the entire timeout window
            await asyncio.sleep(self.timeout)

            self._session_opened = False
            logger.info(f"[Broker] Session ended after {self.timeout} seconds. Checking emitters...")

            # Cancel any remaining uncompleted tasks
            for uuid, task in self._emitter_tasks.items():
                if not task.done():
                    task.cancel()

            all_resolved = len(self.emitted) == len(self.emitters)

            if all_resolved:
                logger.info("[Broker] All emitters resolved. Broadcasting to consumers...")
                await self.event_bus.emit("all_resolved")
            else:
                unresolved = set(self.emitters.keys()) - self.emitted
                logger.warning(f"[Broker] Not all emitters resolved. Unresolved: {unresolved}")

            # Clean up state
            for uuid in list(self.emitted):
                self.emitters.pop(uuid, None)
            self._emitter_tasks.clear()
            self.emitted.clear()

            logger.info("[Broker] Coordination session closed.")
            return all_resolved

__all__ = ("Broker",)
