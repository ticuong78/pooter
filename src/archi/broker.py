import asyncio
from typing import Optional, Callable

from .emitter import Emitter, EmitterFactory
from .consumer import Consumer
from .event import EventBus

class Broker:
    def __init__(self, timeout: float = 1.0, event_bus: Optional[EventBus] = None, emitter_factory: Optional[EmitterFactory] = None):
        self.opened_section = False
        self.emitters: dict[str, Emitter] = {}
        self.emitted: set[str] = set()
        self.consumers: dict[str, Consumer] = {}
        self.timeout = timeout
        self.event_bus = event_bus or EventBus()
        self.emitter_factory = emitter_factory or EmitterFactory()

    def create_emitter(self, resolve_callback: Optional[Callable[[], None]] = None) -> Emitter:
        return self.emitter_factory.create_emitter(resolve_callback=resolve_callback)

    def register_emitter(self, emitter: Emitter):
        self.emitters[emitter.uuid] = emitter
        emitter.broker = self # type: ignore

    def register_consumer(self, consumer: Consumer):
        self.consumers[consumer.uuid] = consumer
        self.event_bus.subscribe("all_resolved", consumer.consume) # type: ignore

    async def collect_emit(self, uuid: str):
        self.opened_section = True
        self.emitted.add(uuid)
        pending = [e for k, e in self.emitters.items() if k not in self.emitted]    

        try:
            await asyncio.gather(*[e.await_resolution(timeout=self.timeout) for e in pending])
            print("[Broker] All emitters resolved. Broadcasting to consumers...")
            await self.event_bus.emit("all_resolved")
        except Exception as e:
            print(f"[Broker] Error during coordination: {e}")
        finally:
            # Only clear state if this was the last emitter
            self.emitted.clear()
            self.opened_section = False

__all__ = ("Broker",)
