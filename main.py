# pyright: reportArgumentType=false

import asyncio
import logging

from src.archi.broker import Broker
from src.archi.emitter import Emitter
from src.archi.consumer import Consumer

logging.basicConfig(level=logging.INFO)

async def main():
    broker = Broker(timeout=5)

    # Create consumer instances
    consumer1 = Consumer("Consumer1")
    consumer2 = Consumer("Consumer2")

    # Register consumers to the broker
    broker.register_consumer(consumer1)
    broker.register_consumer(consumer2)

    # Create emitters and register them to the broker
    emitter1 = Emitter(uuid="emitter1")
    emitter2 = Emitter(uuid="emitter2")
    broker.register_emitter(emitter1)
    broker.register_emitter(emitter2)

    task = emitter1.emit({ "message": "Message one" })

    async def simulate_payloads():
        await emitter2.emit()

    # Run the simulation
    await asyncio.gather(task, simulate_payloads())

    # After the payloads are emitted, check if consumers received them
    print(f"Consumer1 received: {consumer1.payload}")
    print(f"Consumer2 received: {consumer2.payload}")

if __name__ == "__main__":
    asyncio.run(main())
