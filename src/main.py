import warnings
from typing import Annotated
import logging

from fastapi import FastAPI, Request, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi_pagination import add_pagination
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi_pagination.utils import FastAPIPaginationWarning
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

from src.core.config import setting_conn, configure_logging, templates, STATIC_DIR
from src.auth.routers import router as router_auth
from src.core.database import get_async_session
from src.core.jwt_utils import create_jwt, validate_password

# from src.users.crud import (
#     get_user_from_db,
# )
from src.core.exceptions import (
    NotFindUser,
)

# from src.users.models import User
# from src.users.routers import router as router_users
# from src.payments.routers import router as router_payments
# from src.webhooks import webhooks_router
# from src.payments.schemas import PaymentGenerateBaseSchemas, TransactionInSchemas
# from src.utils.processing import generate_payments, process_transaction
from src.core.exceptions import ErrorInData

warnings.simplefilter("ignore", FastAPIPaginationWarning)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

description = """
    API Transactions helps you do awesome stuff. 🚀

    You will be able to:

    * **Read users**
    * **Create/Update/Remove users**
    * **Get list scores user/users**
    * **Get list scores**
    * **Get list payments for user**
    * **Make a transaction**
"""  # noqa: W293

# включение webhooks в документацию
app = FastAPI(
    title="AirportDirectory",
    description=description,
    version="0.1.0",
    docs_url="/docs",
)

# CORS Configuration
origins = ["http://localhost:8000", "http://127.0.0.1:8000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=setting_conn.SECRET_KEY)
# app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(router_auth)

add_pagination(app)

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


@app.get("/")
def index(request: Request):
    user = request.session.get("user")
    if user:
        return RedirectResponse("auth/welcome")

    return templates.TemplateResponse(name="home.html", context={"request": request})


# @app.post(
#     "/token",
#     response_class=JSONResponse,
#     status_code=status.HTTP_202_ACCEPTED,
#     tags=["main"],
# )
# async def login_for_access_token(
#     data_login: Annotated[OAuth2PasswordRequestForm, Depends()],
#     session: AsyncSession = Depends(get_async_session),
# ):
#     try:
#         user: User = await get_user_from_db(session=session, email=data_login.username)
#     except NotFindUser:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"The user with the username: {data_login.username} not found",
#         )
#
#     if await validate_password(
#         password=data_login.password, hashed_password=user.hashed_password.encode()
#     ):
#         access_token: str = await create_jwt(str(user.id))
#
#         resp = JSONResponse({"access_token": access_token, "token_type": "bearer"})
#         resp.set_cookie(key=COOKIE_NAME, value=access_token, httponly=True)
#         return resp
#     else:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Error password for login: {data_login.username}",
#         )


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
