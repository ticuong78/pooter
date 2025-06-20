import logging
import asyncio

from typing import Optional, Callable, TYPE_CHECKING, Any, List
from uuid import uuid4

if TYPE_CHECKING:
    from src.archi.broker import Broker

logger = logging.getLogger(__name__)

class Consumer:
    def __init__(self, uuid: Optional[str] = None, callback: Optional[Callable[[List[Any]], bool]] = None):
        self.uuid = uuid or str(uuid4())
        self.broker: Broker | None = None
        self.callback = callback
        self.payload = None

    async def consume(self, payload: List[Any]):
        self.payload = payload
        if self.callback is not None:
            if asyncio.iscoroutinefunction(self.callback):
                if self.callback is not None:
                    await self.callback(payload)
            else:
                async def wrapper(func):
                    func(payload)
                
                await wrapper(self.callback)

        logger.info(f"[Consumer {self.uuid}] Consumed...")

__all__ = ("Consumer",)