import logging
from typing import Optional

from fastapi import APIRouter, Request, Response, status, Depends
from fastapi.exceptions import HTTPException
from starlette.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User
from src.core.config import (
    setting,
    configure_logging,
    templates,
    oauth_yandex,
    COOKIE_NAME,
)
from src.core.exceptions import ErrorInData, NotFindUser
from src.core.jwt_utils import create_jwt, validate_password
from src.core.database import get_async_session
from src.auth.utils import get_yandex_user_data, get_access_token
from src.auth.schemas import LoginSchemas
from src.users.crud import (
    find_user_by_email,
    create_user_without_password,
    get_user_from_db,
)
from src.users.schemas import UserBaseSchemas


router = APIRouter(prefix="/auth", tags=["auth"])


configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/login", response_class=Response, status_code=status.HTTP_202_ACCEPTED)
async def user_login_by_password(
    request: Request,
    data_login: LoginSchemas,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        user: User = await get_user_from_db(session=session, email=data_login.email)
    except NotFindUser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The user with the username: {data_login.email} not found",
        )

    if await validate_password(
        password=data_login.password, hashed_password=user.hashed_password.encode()
    ):
        access_token: str = await create_jwt(
            user=str(user.id),
            expire_minutes=setting.auth_jwt.access_token_expire_minutes,
        )
        refresh_token: str = await create_jwt(
            user=str(user.id),
            expire_minutes=setting.auth_jwt.refresh_token_expire_minutes,
        )

        user.refresh_token = refresh_token
        await session.commit()

        resp = Response(
            content="The user is logged in",
            status_code=status.HTTP_202_ACCEPTED,
        )
        resp.set_cookie(key=COOKIE_NAME, value=access_token, httponly=True)

        request.session["user"] = {"family_name": user.full_name, "id": str(user.id)}

        return resp
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error password for login: {data_login.email}",
        )


@router.get("/login/yandex")
async def login(request: Request):
    url = request.url_for("auth_yandex")
    return await oauth_yandex.yandex.authorize_redirect(request, url)


@router.get("/yandex")
async def auth_yandex(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    logger.info("Start of user authentication by Yandex.ID")
    try:
        token = await get_access_token(request=request)
    except ErrorInData as exp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{exp}",
        )
    user_data = await get_yandex_user_data(token["access_token"])

    user_email = user_data.get("default_email")
    real_name = user_data.get("real_name")

    user: Optional[User] = await find_user_by_email(session=session, email=user_email)

    if user is None:
        logger.info("User with email %s not found", user_email)
        user: User = await create_user_without_password(
            session=session,
            user_data=UserBaseSchemas(full_name=real_name, email=user_email),
        )
        logger.info("User with email %s created", user_email)

    access_token: str = await create_jwt(
        user=str(user.id), expire_minutes=setting.auth_jwt.access_token_expire_minutes
    )
    refresh_token: str = await create_jwt(
        user=str(user.id), expire_minutes=setting.auth_jwt.refresh_token_expire_minutes
    )

    user.refresh_token = refresh_token
    await session.commit()

    resp: Response = RedirectResponse("welcome")
    resp.set_cookie(key=COOKIE_NAME, value=access_token, httponly=True, samesite="lax")
    request.session["user"] = {"family_name": user.full_name, "id": str(user.id)}

    return resp


@router.get("/logout")
def logout(request: Request):
    resp: Response = RedirectResponse("/")
    resp.delete_cookie(COOKIE_NAME)
    # request.session.pop("user")
    request.session.clear()
    return resp


@router.get(
    "/welcome",
    include_in_schema=False,
)
def welcome(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/")
    return templates.TemplateResponse(
        name="welcome.html", context={"request": request, "user": user}
    )
