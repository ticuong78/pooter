import asyncio
import logging
from typing import Optional, Callable, TYPE_CHECKING
from uuid6 import uuid7

if TYPE_CHECKING:
    from broker import Broker

logger = logging.getLogger(__name__)

class EmitterFactory:
    @staticmethod
    def create_emitter(uuid: Optional[str] = None, resolve_callback: Optional[Callable[[], None]] = None) -> "Emitter":
        emitter = Emitter(uuid)
        emitter.resolve_callback = resolve_callback
        return emitter

class Emitter:
    def __init__(self, uuid: Optional[str] = None):
        self.uuid = uuid or str(uuid7())
        self.broker: Broker | None = None
        self._resolved = asyncio.Event()
        self.resolve_callback: Optional[Callable[[], None]] = None

    async def emit(self):
        if not self.broker:
            raise RuntimeError("Emitter has no broker.")

        try:
            # First emitter: begin coordination
            if not self.broker._session_opened:
                logger.info(f"[Emitter {self.uuid}] emitting (starting session)...")
                return await self.broker.collect_emit(self.uuid)
            else:
                # Called during a session — resolve immediately
                async def wrapper():
                    self._resolve()

                await wrapper()

                return True
        except Exception as e:
            logger.error(f"[Emitter {self.uuid}] Error emitting: {e}")
            return False

    async def await_resolution(self, timeout: float):
        try:
            await asyncio.wait_for(self._resolved.wait(), timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Emitter {self.uuid} timed out")

    def _resolve(self):
        if self.resolve_callback:
            self.resolve_callback()
        self._resolved.set()
        logger.info(f"[Emitter {self.uuid}] resolving (finishing session)...")

__all__ = ("Emitter",)
