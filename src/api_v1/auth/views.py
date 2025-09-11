import logging

import aiohttp
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import URL
from authlib.integrations.starlette_client import OAuthError

from src.api_v1.auth.crud import check_auth_user
from src.api_v1.auth.schemas import AuthUserSchemas, GoogleCallbackSchemas
from src.api_v1.auth.utils import generate_google_oauth_redirect_uri
from src.api_v1.users.schemas import OutUserSchemas, UserInfoSchemas

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
    COOKIE_NAME,
    # templates,
    # COOKIE_NAME,
    configure_logging,
    oauth_yandex,
    setting,
)
from src.core.database import get_async_session, get_cache_connection, get_redis_connection
from src.core.jwt_utils import create_jwt
from src.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])


configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


@router.get("/google/url")
async def get_google_oauth_redirect_uri(db_cache: Redis = Depends(get_cache_connection)):
    uri = await generate_google_oauth_redirect_uri(db_cache)
    return {"url": uri}  # Redirect выполняется на фронтенде


@router.post(
    "/google/callback",
    response_model=OutUserSchemas,
    status_code=status.HTTP_200_OK,
    include_in_schema=True,
)
async def handle_code(
    response: Response,
    request: Request,
    code_state: GoogleCallbackSchemas,
    session: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis_connection),
    db_cache: Redis = Depends(get_cache_connection),
):
    google_state: str = await db_cache.get(code_state.state)

    if google_state is None:
        raise HTTPException(status_code=400, detail="Error state for Google")

    google_token_url = "https://oauth2.googleapis.com/token"

    async with aiohttp.ClientSession() as client:
        async with client.post(
            url=google_token_url,
            data={
                "client_id": setting.google.OAUTH_GOOGLE_CLIENT_ID,
                "client_secret": setting.google.OAUTH_GOOGLE_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": setting.google.GOOGLE_REDIRECT_URI,
                "code": code_state.code,
            },
            ssl=True,  # в разработке ssl=False
        ) as resp:
            response_data = await resp.json()
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
    logger.info("Generate JWT for user by name %s" % user.full_name)
    access_token: str = await create_jwt(
        user=str(user.id),
        expire_minutes=setting.auth_jwt.access_token_expire_minutes,
    )
    refresh_token: str = await create_jwt(
        user=str(user.id),
        expire_minutes=setting.auth_jwt.refresh_token_expire_minutes,
    )

    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=False,  # True в production
        samesite="lax",
        path="/",
    )

    request.session["user"] = {"family_name": user.full_name, "id": str(user.id)}
    await redis.set(str(user.id), refresh_token)

    return OutUserSchemas(
        access_token=access_token,
        token_type="bearer",
        user=UserInfoSchemas(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
        ),
    )


@router.get("/yandex/url")
async def url_yandex(request: Request):
    url: URL = request.url_for("auth_yandex")
    return await oauth_yandex.yandex.authorize_redirect(request, url)


@router.get("/yandex")
async def auth_yandex(
    response: Response,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis_connection),
):
    logger.info("Start of user authentication by Yandex.ID")
    try:
        token = await oauth_yandex.yandex.authorize_access_token(request)
    except OAuthError as exp:
        logger.exception("Error authentication by Yandex.ID", exc_info=exp)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{exp}",
        )

    user_data_full = await oauth_yandex.yandex.parse_id_token(request, token)

    user_data: AuthUserSchemas = AuthUserSchemas(
        name=user_data_full["real_name"],
        email=user_data_full["default_email"],
        picture=user_data_full["default_avatar_id"],
    )

    # найти/зарегистрировать пользователя в БД, вернуть пользователя
    user: User = await check_auth_user(session=session, user_info=user_data)

    # сгенерить токен
    logger.info("Generate JWT for user by name %s" % user.full_name)
    access_token: str = await create_jwt(
        user=str(user.id),
        expire_minutes=setting.auth_jwt.access_token_expire_minutes,
    )
    refresh_token: str = await create_jwt(
        user=str(user.id),
        expire_minutes=setting.auth_jwt.refresh_token_expire_minutes,
    )

    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=False,  # True в production
        samesite="lax",
        path="/",
    )

    request.session["user"] = {"family_name": user.full_name, "id": str(user.id)}
    await redis.set(str(user.id), refresh_token)

    return OutUserSchemas(
        access_token=access_token,
        token_type="bearer",
        user=UserInfoSchemas(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
        ),
    )


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
