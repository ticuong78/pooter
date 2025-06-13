import logging

from uuid6 import uuid7
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from src.archi import Broker

logger = logging.getLogger(__name__)

class Emitter:
    def __init__(self, uuid: str | None) -> None:
        if uuid == None or len(uuid) == 0: # Test, mong đợi uuid thành chuỗi ngẫu nhiên
            uuid = str(uuid7())

        self.broker: Broker | None = None
        self.uuid = uuid

        logging.info(f"[Emitter {self.uuid}] initializing emitter...")

    def regist(self, broker: Broker):
        if broker is None:
            logging.warning(f"[Emitter {self.uuid}] should not regist NULL broker!")

        self.broker = broker

__all__ = ('Emitter',)