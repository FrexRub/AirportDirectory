import logging
from typing import Annotated

import aiohttp
import jwt
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.auth.crud import check_auth_user
from src.api_v1.auth.schemas import AuthUserSchemas
from src.api_v1.auth.utils import generate_google_oauth_redirect_uri

#
# from src.api_v1.users.crud import (
#     create_user_without_password,
#     find_user_by_email,
#     get_user_from_db,
# )
# from src.api_v1.users.schemas import UserBaseSchemas
# from src.api_v1.auth.schemas import LoginSchemas
# from src.api_v1.auth.utils import get_access_token, get_yandex_user_data
from src.core.config import (
    # COOKIE_NAME,
    configure_logging,
    # oauth_yandex,
    setting,
    # templates,
)
from src.core.database import get_async_session

# from src.core.exceptions import ErrorInData
# from src.core.jwt_utils import create_jwt
from src.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])


configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


@router.get("/google/url")
def get_google_oauth_redirect_uri():
    uri = generate_google_oauth_redirect_uri()
    return {"url": uri}  # Redirect выполняется на фронтенде


@router.post("/google/callback")
async def handle_code(
    code: Annotated[str, Body()],
    session: AsyncSession = Depends(get_async_session),
):
    google_token_url = "https://oauth2.googleapis.com/token"

    async with aiohttp.ClientSession() as client:
        async with client.post(
            url=google_token_url,
            data={
                "client_id": setting.google.OAUTH_GOOGLE_CLIENT_ID,
                "client_secret": setting.google.OAUTH_GOOGLE_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": setting.google.GOOGLE_REDIRECT_URI,
                "code": code,
            },
            ssl=False,
        ) as response:
            response_data = await response.json()
            if "access_token" not in response_data:
                raise HTTPException(status_code=400, detail="Error getting access token from Google")

            id_token = response_data["id_token"]

    try:
        user_data_full = jwt.decode(
            id_token,
            algorithms=["RS256"],
            options={"verify_signature": False},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error jwt token from Google",
        )

    user_data: AuthUserSchemas = AuthUserSchemas(
        name=user_data_full["name"],
        email=user_data_full["email"],
        picture=user_data_full["picture"],
    )

    # найти/зарегистрировать пользователя в БД, вернуть пользователя
    user: User = await check_auth_user(session=session, user_info=user_data)
    # сгенерить токен
    return {"user": user}
    #
    # @router.get("/login/yandex")
    # async def login(request: Request):
    #     url = request.url_for("auth_yandex")
    #     return await oauth_yandex.yandex.authorize_redirect(request, url)
    #
    #
    # @router.get("/yandex")
    # async def auth_yandex(
    #     request: Request,
    #     session: AsyncSession = Depends(get_async_session),
    # ):
    #     logger.info("Start of user authentication by Yandex.ID")
    #     try:
    #         token = await get_access_token(request=request)
    #     except ErrorInData as exp:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail=f"{exp}",
    #         )
    #     user_data = await get_yandex_user_data(token["access_token"])
    #
    #     user_email = user_data.get("default_email")
    #     real_name = user_data.get("real_name")
    #
    #     user: Optional[User] = await find_user_by_email(session=session, email=user_email)
    #
    #     if user is None:
    #         logger.info("User with email %s not found", user_email)
    #         user: User = await create_user_without_password(
    #             session=session,
    #             user_data=UserBaseSchemas(full_name=real_name, email=user_email),
    #         )
    #         logger.info("User with email %s created", user_email)
    #
    # access_token: str = await create_jwt(
    #     user=str(user.id),
    #     expire_minutes=setting.auth_jwt.access_token_expire_minutes,
    # )


#     refresh_token: str = await create_jwt(
#         user=str(user.id), expire_minutes=setting.auth_jwt.refresh_token_expire_minutes
#     )
#
#     user.refresh_token = refresh_token
#     await session.commit()
#
#     resp: Response = RedirectResponse("welcome")
#     resp.set_cookie(key=COOKIE_NAME, value=access_token, httponly=True, samesite="lax")
#     request.session["user"] = {"family_name": user.full_name, "id": str(user.id)}
#
#     return resp
#
#
# @router.get(
#     "/welcome",
#     include_in_schema=False,
# )
# def welcome(request: Request):
#     user = request.session.get("user")
#     if not user:
#         return RedirectResponse("/")
#     return templates.TemplateResponse(name="welcome.html", context={"request": request, "user": user})
