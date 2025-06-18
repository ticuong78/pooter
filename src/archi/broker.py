import asyncio
import logging
from typing import Optional, Callable, Dict
from uuid6 import uuid7

from .emitter import Emitter, EmitterFactory
from .consumer import Consumer
from .event import EventBus

logger = logging.getLogger(__name__)

class BrokerFactory:
    @staticmethod
    def create_broker(
        uuid: Optional[str] = None,
        timeout: float = 1.0,
        event_bus: Optional[EventBus] = None,
        emitter_factory: Optional[EmitterFactory] = None
    ) -> "Broker":
        return Broker(
            uuid=uuid or str(uuid7()),
            timeout=timeout,
            event_bus=event_bus or EventBus(),
            emitter_factory=emitter_factory or EmitterFactory()
        )

class BrokerManager:
    def __init__(self):
        self._brokers: Dict[str, Broker] = {}

    def create_broker(self, uuid: Optional[str] = None, timeout: float = 1.0):
        if uuid in self._brokers:
            return self.get_broker(uuid)

        broker = BrokerFactory.create_broker(uuid=uuid, timeout=timeout)

        self._brokers[broker.uuid] = broker
        logger.info(f"[BrokerManager] Created and added broker with UUID: {broker.uuid}")
        return broker

    def register_broker(self, broker: "Broker"):
        # Tạo broker qua factory
        if broker.uuid in self._brokers:
            raise ValueError(f"Broker with UUID {broker.uuid} already exists.")

        self._brokers[broker.uuid] = broker
        logger.info(f"[BrokerManager] Created and added broker with UUID: {broker.uuid}")

    def get_broker(self, uuid: str) -> Optional["Broker"]:
        return self._brokers.get(uuid)

    def remove_broker(self, uuid: str) -> bool:
        if uuid in self._brokers:
            del self._brokers[uuid]
            logger.info(f"[BrokerManager] Removed broker with UUID: {uuid}")
            return True
        return False

    def register_emitter_to(self, broker_uuid: str, emitter: Emitter):
        broker = self.get_broker(broker_uuid)
        if not broker:
            raise ValueError(f"No broker found with UUID: {broker_uuid}")
        broker.register_emitter(emitter)
        logger.info(f"[BrokerManager] Registered emitter {emitter.uuid} to broker {broker_uuid}")

    def update_broker_timeout(self, uuid: str, timeout: float):
        broker = self.get_broker(uuid)
        if broker:
            broker.timeout = timeout
            logger.info(f"[BrokerManager] Updated timeout for broker {uuid} to {timeout}")

    def get_all_brokers(self) -> list["Broker"]:
        return list(self._brokers.values())

class Broker:
    def __init__(self, uuid: Optional[str] = None, timeout: float = 1.0, event_bus: Optional[EventBus] = None, emitter_factory: Optional[EmitterFactory] = None):
        self.uuid = uuid or str(uuid7())
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
        if emitter.broker is not None and emitter.broker is not self:
            logger.warning(f"[Broker {self.uuid}] Cannot register emitter {emitter.uuid}: already attached to another broker.")
            return

        if self._session_opened:
            logger.warning(f"[Broker {self.uuid}] Broker is opening a session, please register again later.")
            return

        self.emitters[emitter.uuid] = emitter
        emitter.broker = self

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
        async with self._session_lock:
            self._session_opened = True
            self.emitted.add(uuid)

            pending = [e for k, e in self.emitters.items() if k not in self.emitted]

            try:
                await asyncio.gather(*[e.await_resolution(timeout=self.timeout) for e in pending])
                print("[Broker] All emitters resolved. Broadcasting to consumers...")
                await self.event_bus.emit("all_resolved")
                return True
            except Exception as e:
                print(f"[Broker] Error during coordination: {e}")
                return False
            finally:
                self._session_opened = False
                self.emitted.clear()

__all__ = ("Broker",)
