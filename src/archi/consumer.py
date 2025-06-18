import logging
import asyncio

from typing import Optional, Coroutine, TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from src.archi.broker import Broker

logger = logging.getLogger(__name__)

class Consumer:
    def __init__(self, uuid: Optional[str] = None, callback: Optional[Coroutine[any, any, any]] = None):
        self.uuid = uuid or str(uuid4())
        self.broker: Broker | None = None
        self.callback = callback

    async def consume(self):
        if self.callback is not None:
            if asyncio.iscoroutinefunction(self.callback):
                await self.callback()
            else:
                async def wrapper(func):
                    func()
                
                await wrapper(self.callback)

        logger.info(f"[Consumer {self.uuid}] Consumed...")

__all__ = ("Consumer",)