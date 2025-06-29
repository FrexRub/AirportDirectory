import logging
from typing import Optional

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.exceptions import HTTPException
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.users.crud import (
    create_user,
    find_user_by_email,
    get_user_from_db,
    update_user_db,
)
from src.api_v1.users.schemas import (
    LoginSchemas,
    OutUserSchemas,
    UserBaseSchemas,
    UserCreateSchemas,
    UserInfoSchemas,
    UserUpdatePartialSchemas,
    UserUpdateSchemas,
)
from src.core.config import COOKIE_NAME, configure_logging, setting
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
from src.core.jwt_utils import create_jwt, validate_password
from src.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


@router.get(
    "/me",
    response_model=UserBaseSchemas,
    status_code=status.HTTP_200_OK,
)
async def get_info_about_me(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user_authorization),
) -> UserBaseSchemas:
    """
    Возвращает информацию об авторизованном пользователе
    """
    find_user: Optional[User] = await find_user_by_email(session=session, email=user.email)
    if find_user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user not found",
        )
    return UserBaseSchemas(**find_user.__dict__)


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
            user=UserInfoSchemas(id=str(user.id), email=data_login.username, full_name=user.full_name),
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
    try:
        user: User = await create_user(session=session, user_data=new_user)
    except EmailInUse:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The email address is already in use",
        )
    except ErrorInData as exp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{exp}",
        )
    else:
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
            user=UserInfoSchemas(id=str(user.id), email=new_user.email, full_name=new_user.full_name),
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
