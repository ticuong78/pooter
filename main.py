# pyright: reportArgumentType=false

import asyncio
import logging

from src.archi.broker import Broker
from src.archi.emitter import Emitter
from src.archi.consumer import Consumer

logging.basicConfig(level=logging.INFO)

async def main():
    async def callback_consumer():
        await asyncio.sleep(0.5)
        print("Dũng xấu trai")
    
    def callback_consumer_2():
        print("Quyên đẹp trai")
    
    broker = Broker(timeout=1.0)

    emitter1 = Emitter("ONE")
    emitter2 = Emitter("TWO")
    consumer1 = Consumer(callback=callback_consumer)
    consumer2 = Consumer(callback=callback_consumer_2)

    broker.register_emitter(emitter1)
    broker.register_emitter(emitter2)
    broker.register_consumer(consumer1)
    broker.register_consumer(consumer2)

    # Start emitter1 (this starts the coordination session)
    emitter1_task = emitter1.emit()  # async def emit()

    # Emit emitter2 before timeout
    async def emit_emitter2():
        await asyncio.sleep(0.2)
        await emitter2.emit()

    # Register emitter3 after session starts, then emit
    async def register_and_emit_emitter3():
        await asyncio.sleep(0.3)  # after session starts
        emitter3 = Emitter("THREE")
        emitter3.resolve_callback = lambda uuid=emitter3.uuid: print(f"[Emitter {uuid}] internal resolved.")
        broker.register_emitter(emitter3)

        await asyncio.sleep(0.4) # this should be enough to resolve emitter3
        # await asyncio.sleep(0.4) # otherwise, this will be ignored
        await emitter3.emit()

    await asyncio.gather(emitter1_task, emit_emitter2(), register_and_emit_emitter3())

if __name__ == "__main__":
    asyncio.run(main())
