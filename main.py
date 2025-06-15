# pyright: reportArgumentType=false

import asyncio
import logging

from src.archi.broker import Broker
from src.archi.emitter import Emitter
from src.archi.consumer import Consumer

# Set up logging for visibility
logging.basicConfig(level=logging.INFO)

async def main():
    broker = Broker(timeout=1.0)

    emitter1 = Emitter()
    emitter2 = Emitter()

    # decide what the Emitters do on resolve_callback
    emitter2.resolve_callback = lambda uuid=emitter2.uuid: print(f"[Emitter {uuid}] internal resolved.") 

    consumer1 = Consumer()
    consumer2 = Consumer()

    broker.register_emitter(emitter1)
    broker.register_emitter(emitter2)
    broker.register_consumer(consumer1)
    broker.register_consumer(consumer2)

    # Use the awaited API (Option A)
    emitter1_task = emitter1.emit()  # async def emit()
    
    # Resolve the other emitter after delay
    async def delayed():
        await asyncio.sleep(0.3)
        await emitter2.emit()

    await asyncio.gather(delayed(), emitter1_task) 

if __name__ == "__main__":
    asyncio.run(main())