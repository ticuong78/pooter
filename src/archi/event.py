import inspect
import asyncio

from typing import Callable
from collections import defaultdict

class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable[[], None]]] = defaultdict(list)

    def subscribe(self, event: str, handler: Callable[[], None]):
        self._subscribers.setdefault(event, []).append(handler)

    async def emit(self, event: str):
        tasks = []
        for handler in self._subscribers.get(event, []):
            if inspect.iscoroutinefunction(handler):
                tasks.append(handler())
            else:
                # wrap sync function
                tasks.append(asyncio.to_thread(handler))

        await asyncio.gather(*tasks)

__all__ = ("EventBus",)