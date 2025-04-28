from typing import Annotated, Optional
from uuid import UUID

import jwt
from fastapi import Depends, status, Path, Request, Response
from fastapi.exceptions import HTTPException
from fastapi.security import APIKeyCookie

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.core.config import COOKIE_NAME, setting
from src.core.jwt_utils import decode_jwt, create_jwt
from src.api_v1.users.crud import get_user_by_id
from src.models.user import User

cookie_scheme = APIKeyCookie(name=COOKIE_NAME)


async def current_user_authorization(
    request: Request,
    response: Response,
    token: str = Depends(cookie_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> User:

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authorized"
        )

    try:
        payload = await decode_jwt(token)
    except jwt.ExpiredSignatureError:
        # получаем пользователя по ID из сессии
        id_user: UUID = UUID(request.session["user"].get("id"))
        user: User = await get_user_by_id(session=session, id_user=id_user)

        # проверяем наличие refresh_token
        if user.refresh_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authorized"
            )
        # извлекаем данные из refresh_token
        try:
            payload = await decode_jwt(user.refresh_token)
        except jwt.ExpiredSignatureError:
            # в случае экспирации токена авторизируемся заново
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired. Please login again",
            )
        else:
            access_token: str = await create_jwt(
                user=str(user.id),
                expire_minutes=setting.auth_jwt.access_token_expire_minutes,
            )
            response.set_cookie(key=COOKIE_NAME, value=access_token, httponly=True)
            return user

    else:
        id_user = UUID(payload["sub"])
    return await get_user_by_id(session=session, id_user=id_user)


async def current_superuser_user(
    request: Request,
    token: str = Depends(cookie_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authorized"
        )

    try:
        payload = await decode_jwt(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )

    id_user = UUID(payload["sub"])
    user: User = await get_user_by_id(session=session, id_user=id_user)

    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user is not an administrator",
        )
    return user


async def user_by_id(
    id_user: Annotated[UUID, Path],
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user_authorization),
) -> User:
    find_user: Optional[User] = await get_user_by_id(session=session, id_user=id_user)
    if find_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id_user} not found!",
        )
    if user.id == id_user or user.is_superuser:
        return find_user
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough rights",
        )
