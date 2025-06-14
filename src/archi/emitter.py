import asyncio

from typing import Optional, Callable, TYPE_CHECKING
from uuid6 import uuid7

if TYPE_CHECKING:
    from broker import Broker

class Emitter:
    def __init__(self, uuid: Optional[str] = None):
        self.uuid = uuid or str(uuid7())
        self.broker: Broker | None = None
        self._resolved = asyncio.Event()
        self.resolve_callback: Optional[Callable[[], None]] = None

    async def emit(self):
        if not self.broker:
            raise RuntimeError("Emitter has no broker.")
        print(f"[Emitter {self.uuid}] emitting...")
        await self.broker.collect_emit(self.uuid)

    async def await_resolution(self, timeout: float):
        try:
            await asyncio.wait_for(self._resolved.wait(), timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Emitter {self.uuid} timed out")

    def resolve(self):
        if self.resolve_callback:
            self.resolve_callback()
        self._resolved.set()
        print(f"[Emitter {self.uuid}] resolving...")


__all__ = ("Emitter",)