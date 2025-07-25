import logging
import warnings

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
from fastapi_pagination.utils import FastAPIPaginationWarning
from starlette.middleware.sessions import SessionMiddleware

from src.api_v1 import router as api_router
from src.core.config import configure_logging, setting

description = """
    API airport directory

    You will be able to:

    * **Read users**
    * **Create/Update/Remove users**
    * **Load file**
"""

warnings.simplefilter("ignore", FastAPIPaginationWarning)

app = FastAPI(
    title="API_AirportDirectory",
    description=description,
    version="0.1.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
        # "http://localhost:8000",
        # "https://airportcards.ru",
        # "https://www.airportcards.ru",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=setting.secret_key.get_secret_value())

app.include_router(router=api_router)

add_pagination(app)

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
