import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

from src.api_v1 import router as api_router
from src.core.config import STATIC_DIR, configure_logging, setting_conn

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

app.add_middleware(SessionMiddleware, secret_key=setting_conn.SECRET_KEY)

staticfiles = StaticFiles(directory=STATIC_DIR)
template = Jinja2Templates(directory=STATIC_DIR)

app.mount("/static", staticfiles, name="static")

app.include_router(router=api_router)

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


# @app.get("/", response_class=HTMLResponse)
# def main_page(request: Request):
#     logger.info(f"start site")
#     return template.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
