from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from src.archi.broker import Broker
from src.archi.emitter import Emitter

import logging
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # before

    global broker

    broker = Broker()
    # session = SessionManagement(broker=broker)

    # session.open_session()

    yield

    # after

app = FastAPI(lifespan=lifespan)

@app.post("/regist_emitter")
def regist_emitter():
    try:
        emitter = Emitter()
        broker.register_emitter(emitter)

        logger.info("Successfully registered emitter")
        return JSONResponse(content={"message": "Successfully registered emitter"}, status_code=201)
    except Exception as e:
        logger.error("Failed to register emitter")
        return JSONResponse(content={"message": "Failed to register emitter"}, status_code=400)

def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the FastAPI server"""
    uvicorn.run(
        app,
        host=host,
        port=port,
        # reload=True
    )

if __name__ == "__main__":
    start_server() 