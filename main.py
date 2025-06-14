# pyright: reportArgumentType=false

import asyncio
import logging

from src.archi.broker import Broker
from src.archi.emitter import Emitter
from src.archi.consumer import Consumer

# Set up logging for visibility
logging.basicConfig(level=logging.INFO)

async def main():
    # 1. Create the broker
    broker = Broker(timeout_ms=1000)

    # 2. Create emitters
    emitter1 = Emitter()
    emitter2 = Emitter()

    # 3. Create a consumer
    consumer = Consumer()

    # 4. Register emitters and consumers with the broker
    broker.register_emitter([emitter1, emitter2])
    broker.register_consumer(consumer)

    # 5. Configure emitter2 to resolve itself after some time
    def auto_resolve():
        print(f"[Emitter {emitter2.uuid}] auto-resolving after delay")
    
    emitter2.internal_resolve = auto_resolve

    async def delayed_resolve():
        await asyncio.sleep(0.5)
        emitter2.resolve()

    # 6. Trigger emitter1
    print(f"[Main] Triggering emitter1.emit()")
    emitter1.emit()

    # 7. Start the delayed resolution of emitter2
    asyncio.create_task(delayed_resolve())

    # 8. Give enough time for everything to resolve
    await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
