import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from redis import asyncio as aioredis
import uvicorn

from src.api_v1 import router as api_router
from src.core.config import configure_logging, setting_conn

description = """
    API airport directory

    You will be able to:

    * **Read users**
    * **Create/Update/Remove users**
    * **Load file**
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # redis для refresh_token
    redis = aioredis.from_url(
        f"redis://{setting_conn.REDIS_HOST}:{setting_conn.REDIS_PORT}/1",
        encoding="utf8",
        decode_responses=True,
    )
    yield


app = FastAPI(
    lifespan=lifespan,
    title="API_AirportDirectory",
    description=description,
    version="0.1.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=setting_conn.SECRET_KEY)

app.include_router(router=api_router)

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
