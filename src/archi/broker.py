import logging

from typing import List, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from src.archi import Emitter, Consumer

logger = logging.getLogger(__name__)

class Broker:
    def __init__(
        self, 
        emitters: dict[str, Emitter] = {}, 
        consumers: List[Consumer] = [],
        timeOut: int = 500
    ) -> None:
        self.timeOut: int = timeOut
        self.emitters: dict[str, Emitter] = emitters
        self.emitted: Set[str] = set()
        self.consumers: List[Consumer] = consumers

        logging.info(f"[Broker] initializing broker...")

    def receiveEmit(self, uuid: str) -> None:
        if uuid not in self.emitters.keys():
            logger.error(f"[Broker] {uuid} is not registered.")
            return

    def putIntoPromise(self):
        pass

    def registEmitters(self, emitters: List[Emitter]) -> None:
        for emitter in emitters:
            self.emitters[emitter.uuid] = emitter

    def registConsumer(self, consumers: List[Consumer]) -> None:
        self.consumers.append(*consumers)

__all__ = ('Broker',)