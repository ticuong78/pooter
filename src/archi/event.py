import inspect
import asyncio

from typing import Callable, List, Any
from collections import defaultdict

class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable[[], None]]] = defaultdict(list)

    def subscribe(self, event: str, handler: Callable[[], None]):
        self._subscribers.setdefault(event, []).append(handler)

    async def emit(self, event: str, payloads: List[Any]):
        tasks = []
        # print(payloads)
        for handler in self._subscribers.get(event, []):
            if inspect.iscoroutinefunction(handler):
                tasks.append(handler(payloads)) # type: ignore
            else:
                # wrap sync function
                tasks.append(asyncio.to_thread(handler, payloads)) # type: ignore

        await asyncio.gather(*tasks)

__all__ = ("EventBus",)