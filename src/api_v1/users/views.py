import logging

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


from src.core.database import get_async_session
from src.core.config import configure_logging
from src.core.exceptions import (
    ErrorInData,
    EmailInUse,
    UniqueViolationError,
)
from src.api_v1.users.crud import (
    create_user,
    get_users,
    update_user_db,
    delete_user_db,
    find_user_by_email,
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
)

router = APIRouter(prefix="/users", tags=["Users"])

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


@router.get(
    "/list",
    response_model=list[OutUserSchemas],
    status_code=status.HTTP_200_OK,
)
async def get_list_users(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_superuser_user),
):
    return await get_users(session=session)


@router.get(
    "/me",
    response_model=OutUserSchemas,
    status_code=status.HTTP_200_OK,
)
async def get_info_about_me(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user_authorization),
):
    return await find_user_by_email(session=session, email=user.email)


@router.post(
    "/create",
    response_model=OutUserSchemas,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def user_create(
    new_user: UserCreateSchemas,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_superuser_user),
):
    try:
        result: User = await create_user(session=session, user_data=new_user)
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
        return result


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
