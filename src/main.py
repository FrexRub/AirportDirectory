from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api_v1 import router as api_router

description = """
    API airport directory

    You will be able to:

    * **Read users**
    * **Create/Update/Remove users**
    * **Load file**
"""

app = FastAPI(
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

app.include_router(router=api_router)
