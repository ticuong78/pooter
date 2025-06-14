import logging
import asyncio

from uuid import uuid4
from typing import Optional

from _stub.broker import Broker

logger = logging.getLogger(__name__)

class Consumer:
    def __init__(self, uuid: Optional[str] = None):
        self._uuid = uuid or str(uuid4())
        self._broker: Optional[Broker] = None

    @property
    def uuid(self) -> str:
        return self._uuid

    def register(self, broker: Broker):
        self._broker = broker

    async def consume(self):
        logger.info(f"[Consumer] {self._uuid} consuming...")
        # simulate async processing
        await asyncio.sleep(0.1)
