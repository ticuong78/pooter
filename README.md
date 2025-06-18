# Pooter — Async Event Coordination System

![Test Status](https://github.com/ticuong78/pooter/actions/workflows/module-test.yml/badge.svg)
![License](https://img.shields.io/github/license/ticuong78/pooter)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![PyPI - Version](https://img.shields.io/pypi/v/pooter)

Pooter is an **asynchronous coordination system** built on a simple but powerful pattern:

> Emitter → Broker → Consumer

We call this _"Event Architecture based on Promises"_ — where multiple `Emitter`s notify a `Broker`, which then synchronizes and dispatches events to `Consumer`s once all conditions are fulfilled.

This pattern works on letting an `Emitter` emits the `Broker` then the `Broker` puts all of the other `Emitter`s into the same **Promise**s, which they promise to give give back the same signal (which is **emit**).

If all resolve, the promising section is finished, otherwise, it's cancelled by the `Broker`.

---

## ✨ Features

- Broker-based event coordination
- Awaitable emit + resolution logic
- Modular `EventBus` pub/sub pattern
- Fully tested with `pytest-asyncio`

---

## 📦 Installation

```bash
pip install pooter
```

Or for development:

```bash
git clone https://github.com/ticuong78/pooter
cd pooter
pip install -e .[dev]
```

---

## 🚀 Usage Example

```python
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
```

---

## 🧪 Running Tests

```bash
pytest tests
```

Includes:

- `tests/test_broker.py`
- `tests/test_emitter.py`
- `tests/test_consumer.py`
- `tests/test_events.py`

---

## 📁 Project Structure

```
src/
├── archi/
│   ├── broker.py       # Orchestrates emitter/consumer coordination
│   ├── emitter.py      # Emits to broker
│   ├── consumer.py     # Handles post-resolution logic
│   └── events.py       # Internal event bus
tests/
    └── test_*.py       # Full pytest-asyncio test suite
main.py                 # Example use case
pyproject.toml          # Build + metadata
```

---

## 📜 License

MIT License.  
Created by **Lê Cường** — [cuongdayne17@gmail.com](mailto:cuongdayne17@gmail.com)

---

## 🛠️ Contributing

Contributions are welcome and encouraged.

If you'd like to contribute to `pooter`, please follow these steps:

1. **Fork** the repository
2. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Write clear, tested code
4. Follow existing code style (`black`, `ruff`, `mypy`)
5. Submit a Pull Request with a clear description

Please make sure all tests pass before submitting:

```bash
pytest
```

To run style checks:

```bash
black . && ruff . && mypy src/
```

> For ideas, bugs, or PRs, visit: [github.com/ticuong78/pooter](https://github.com/ticuong78/pooter)
