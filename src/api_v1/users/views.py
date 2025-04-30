import logging

from fastapi import APIRouter, Depends, status, Response, Request
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.core.config import configure_logging, setting, COOKIE_NAME
from src.core.exceptions import (
    ErrorInData,
    EmailInUse,
    UniqueViolationError,
    NotFindUser,
)
from src.api_v1.users.crud import (
    create_user,
    get_users,
    update_user_db,
    delete_user_db,
    find_user_by_email,
    get_user_from_db,
)
from src.core.depends import (
    current_superuser_user,
    current_user_authorization,
    user_by_id,
)
from src.models.user import User
from src.api_v1.users.schemas import (
    UserCreateSchemas,
    OutUserSchemas,
    UserUpdateSchemas,
    UserUpdatePartialSchemas,
    UserInfoSchemas,
    LoginSchemas,
)
from src.core.jwt_utils import create_jwt, validate_password

router = APIRouter(prefix="/users", tags=["Users"])

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


@router.get(
    "/me",
    response_model=UserInfoSchemas,
    status_code=status.HTTP_200_OK,
)
async def get_info_about_me(
        session: AsyncSession = Depends(get_async_session),
        user: User = Depends(current_user_authorization),
):
    return await find_user_by_email(session=session, email=user.email)


@router.post(
    "/login", response_model=OutUserSchemas, status_code=status.HTTP_202_ACCEPTED
)
async def user_login(
        response: Response,
        request: Request,
        data_login: LoginSchemas,
        session: AsyncSession = Depends(get_async_session),
):
    logger.info(f"start login {data_login.username}")

    try:
        user: User = await get_user_from_db(session=session, email=data_login.username)
    except NotFindUser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The user with the username: {data_login.username} not found",
        )

    if await validate_password(
            password=data_login.password, hashed_password=user.hashed_password
    ):
        access_token: str = await create_jwt(
            user=str(user.id),
            expire_minutes=setting.auth_jwt.access_token_expire_minutes,
        )
        refresh_token: str = await create_jwt(
            user=str(user.id),
            expire_minutes=setting.auth_jwt.refresh_token_expire_minutes,
        )

        response.set_cookie(
            key=COOKIE_NAME, value=access_token, httponly=True, samesite="strict"
        )
        request.session["user"] = {"family_name": user.full_name, "id": str(user.id)}

        logger.info(f"User {data_login.username} logged in")

        return OutUserSchemas(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserInfoSchemas(email=data_login.username, full_name=user.full_name),
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
):
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
            key=COOKIE_NAME, value=access_token, httponly=True, samesite="strict"
        )

        request.session["user"] = {"family_name": user.full_name, "id": str(user.id)}

        return OutUserSchemas(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserInfoSchemas(email=new_user.email, full_name=new_user.full_name),
        )


@router.get("/logout", status_code=status.HTTP_200_OK)
def logout(request: Request, response: Response):
    response.delete_cookie(COOKIE_NAME)
    request.session.clear()



@router.delete("/{id_user}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
        user: User = Depends(user_by_id),
        super_user: User = Depends(current_superuser_user),
        session: AsyncSession = Depends(get_async_session),
) -> None:
    await delete_user_db(session=session, user=user)


@router.put(
    "/{id_user}/", response_model=OutUserSchemas, status_code=status.HTTP_200_OK
)
async def update_user(
        user_update: UserUpdateSchemas,
        user: User = Depends(user_by_id),
        session: AsyncSession = Depends(get_async_session),
):
    try:
        res = await update_user_db(session=session, user=user, user_update=user_update)
    except UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Duplicate email",
        )
    else:
        return res


@router.patch(
    "/{id_user}/", response_model=OutUserSchemas, status_code=status.HTTP_200_OK
)
async def update_user_partial(
        user_update: UserUpdatePartialSchemas,
        user: User = Depends(user_by_id),
        session: AsyncSession = Depends(get_async_session),
):
    try:
        res = await update_user_db(
            session=session, user=user, user_update=user_update, partial=True
        )
    except UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Duplicate email",
        )
    else:
        return res
