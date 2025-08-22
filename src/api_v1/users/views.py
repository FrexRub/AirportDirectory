import logging
from typing import Optional
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, Request, Response, Security, status
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.users.crud import (
    confirm_user,
    create_user,
    find_user_by_email,
    get_user_by_id,
    get_user_from_db,
    update_user_db,
)
from src.api_v1.users.schemas import (
    LoginSchemas,
    OutUserSchemas,
    TokenSchemas,
    UserCreateSchemas,
    UserInfoSchemas,
    UserUpdatePartialSchemas,
    UserUpdateSchemas,
)
from src.core.config import COOKIE_NAME, api_key_header, configure_logging, setting
from src.core.database import get_async_session, get_redis_connection
from src.core.depends import (
    current_user_authorization,
    user_by_id,
)
from src.core.exceptions import (
    EmailInUse,
    ErrorInData,
    NotFindUser,
    UniqueViolationError,
)
from src.core.jwt_utils import create_jwt, decode_jwt, validate_password
from src.models.user import User
from src.tasks.tasks import send_email_about_registration

router = APIRouter(prefix="/users", tags=["Users"])

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


@router.get(
    "/register_confirm",
    status_code=status.HTTP_200_OK,
)
async def get_register_confirm(
    token: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Подтверждение регистрации пользователя через почту
    """
    try:
        await confirm_user(session=session, token=token)
    except ErrorInData:
        redirect_url = "https://airportcards.ru/?error=invalid_token"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    else:
        return RedirectResponse(url="https://airportcards.ru/?success=true", status_code=status.HTTP_302_FOUND)


@router.get(
    "/mail_confirm",
    response_model=TokenSchemas,
    status_code=status.HTTP_200_OK,
)
async def get_mail_confirm(
    response: Response,
    session: AsyncSession = Depends(get_async_session),
    authorization_header: str = Security(api_key_header),
):
    """
    Запрос на подтверждение почты
    """
    if authorization_header is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authorized")

    if "Bearer " not in authorization_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authorized")

    token = authorization_header.replace("Bearer ", "")

    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authorized")

    try:
        payload = await decode_jwt(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please login again",
        )
    except jwt.DecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error in request",
        )

    id_user = UUID(payload["sub"])
    user: Optional[User] = await get_user_by_id(session=session, id_user=id_user)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    logger.info("Generate new JWT for user by name %s" % user.full_name)
    access_token: str = await create_jwt(
        user=str(user.id),
        expire_minutes=setting.auth_jwt.access_token_expire_minutes,
    )

    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=False,  # True в production
        samesite="lax",
        path="/",
    )

    send_email_about_registration.delay(
        topic="confirm",
        email_user=user.email,
        name_user=user.full_name,
        token=access_token,
    )
    return TokenSchemas(access_token=access_token)


@router.get(
    "/me",
    response_model=UserInfoSchemas,
    status_code=status.HTTP_200_OK,
)
async def get_info_about_me(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user_authorization),
) -> UserInfoSchemas:
    """
    Возвращает информацию об авторизованном пользователе
    """
    find_user: Optional[User] = await find_user_by_email(session=session, email=user.email)
    if find_user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user not found",
        )

    return UserInfoSchemas(
        id=str(find_user.id),
        email=find_user.email,
        full_name=find_user.full_name,
        is_active=find_user.is_active,
        is_verified=find_user.is_verified,
    )


@router.post("/login", response_model=OutUserSchemas, status_code=status.HTTP_202_ACCEPTED)
async def user_login(
    response: Response,
    request: Request,
    data_login: LoginSchemas,
    session: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis_connection),
) -> OutUserSchemas:
    """
    Логирование пользователя
    """
    logger.info(f"start login {data_login.username}")

    try:
        user: User = await get_user_from_db(session=session, email=data_login.username)
    except NotFindUser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The user with the username: {data_login.username} not found",
        )

    if await validate_password(password=data_login.password, hashed_password=user.hashed_password):
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

        logger.info(f"User {data_login.username} logged in")

        return OutUserSchemas(
            access_token=access_token,
            token_type="bearer",
            user=UserInfoSchemas(
                id=str(user.id),
                email=data_login.username,
                full_name=user.full_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
            ),
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error password for login: {data_login.username}",
        )


@router.post(
    "/register",
    response_model=OutUserSchemas,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=True,
)
async def user_register(
    response: Response,
    request: Request,
    new_user: UserCreateSchemas,
    session: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis_connection),
) -> OutUserSchemas:
    """
    Регистрация пользователе
    """
    logger.info("Start of registration of a new user by name %s" % new_user.full_name)
    try:
        user: User = await create_user(session=session, user_data=new_user)
    except EmailInUse:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Данный адрес электронной почты уже используется",
        )
    except ErrorInData as exp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{exp}",
        )
    else:
        logger.info("Generate JWT for user by name %s" % new_user.full_name)
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

        logger.info("Sending a user registration email")
        send_email_about_registration.delay(
            topic="confirm",
            email_user=new_user.email,
            name_user=new_user.full_name,
            token=access_token,
        )

        return OutUserSchemas(
            access_token=access_token,
            token_type="bearer",
            user=UserInfoSchemas(
                id=str(user.id),
                email=new_user.email,
                full_name=new_user.full_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
            ),
        )


@router.get("/logout", status_code=status.HTTP_200_OK)
def logout(request: Request, response: Response) -> None:
    """
    Обрабатывает выход пользователя из системы.
    """
    response.delete_cookie(COOKIE_NAME)
    request.session.clear()


@router.put("/{id_user}/", response_model=UserInfoSchemas, status_code=status.HTTP_200_OK)
async def update_user(
    user_update: UserUpdateSchemas,
    user: User = Depends(user_by_id),
    session: AsyncSession = Depends(get_async_session),
) -> UserInfoSchemas:
    """
    Переписывает данные пользователе
    """
    try:
        res = await update_user_db(session=session, user=user, user_update=user_update)
    except UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate email",
        )
    else:
        return UserInfoSchemas(**res.__dict__)


@router.patch("/{id_user}/", response_model=UserInfoSchemas, status_code=status.HTTP_200_OK)
async def update_user_partial(
    user_update: UserUpdatePartialSchemas,
    user: User = Depends(user_by_id),
    session: AsyncSession = Depends(get_async_session),
) -> UserInfoSchemas:
    """
    Редактирует данные пользователе
    """
    try:
        res = await update_user_db(session=session, user=user, user_update=user_update, partial=True)
    except UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate email",
        )
    else:
        return UserInfoSchemas(**res.__dict__)
