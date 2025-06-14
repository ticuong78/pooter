import logging
import asyncio

from uuid6 import uuid7
from typing import Callable, Optional

from _stub.broker import Broker

logger = logging.getLogger(__name__)

class Emitter:
    def __init__(self, uuid: Optional[str] = None):
        self._uuid = uuid or str(uuid7())
        self._broker: Optional[Broker] = None
        self.internal_resolve: Optional[Callable[[], None]] = None
        self.external_resolve: Optional[Callable[[], None]] = None

        logger.info(f"[Emitter] Initialized with UUID: {self._uuid}")

    @property
    def uuid(self) -> str:
        return self._uuid

    def register(self, broker: Broker):
        self._broker = broker
        logger.info(f"[Emitter] {self._uuid} registered with broker.")

    def emit(self):
        if not self._broker:
            raise RuntimeError("Emitter not registered with broker.")
        asyncio.create_task(self._broker.collect_emit(self._uuid))

    def resolve(self):
        logger.info(f"[Emitter] {self._uuid} resolving...")
        if self.internal_resolve:
            self.internal_resolve()

        if self.external_resolve:
            self.external_resolve()
