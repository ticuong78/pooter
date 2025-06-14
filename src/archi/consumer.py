import logging

from typing import Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

class Consumer:
    def __init__(self, uuid: Optional[str] = None):
        self.uuid = uuid or str(uuid4())

    async def consume(self):
        logger.info(f"[Consumer {self.uuid}] Consuming...")

__all__ = ("Consumer",)