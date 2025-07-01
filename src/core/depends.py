from typing import Annotated, Optional
from uuid import UUID

import jwt
from fastapi import Depends, Path, Request, Response, Security, status
from fastapi.exceptions import HTTPException
from fastapi.security.api_key import APIKeyHeader
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.users.crud import get_user_by_id
from src.core.database import get_async_session, get_redis_connection
from src.core.jwt_utils import decode_jwt
from src.models.user import User

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


async def current_user_authorization(
    request: Request,
    response: Response,
    authorization_header: str = Security(api_key_header),
    redis: Redis = Depends(get_redis_connection),
    session: AsyncSession = Depends(get_async_session),
) -> Optional[User]:
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

        # # получаем пользователя по ID из сессии
        # id_user: UUID = UUID(request.session["user"].get("id"))
        #
        # # получаем refresh_token по id user
        # refresh_token = await redis.get(str(id_user))
        #
        # # проверяем наличие refresh_token
        # if refresh_token is None:
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authorized"
        #     )
        # # извлекаем данные из refresh_token
        # try:
        #     payload = await decode_jwt(refresh_token)
        # except jwt.ExpiredSignatureError:
        #     # в случае экспирации токена авторизируемся заново
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED,
        #         detail="Session expired. Please login again",
        #     )
        # else:
        #     id_user = UUID(payload["sub"])
        #     user: User = await get_user_by_id(session=session, id_user=id_user)
        #
        #     access_token: str = await create_jwt(
        #         user=str(user.id),
        #         expire_minutes=setting.auth_jwt.access_token_expire_minutes,
        #     )
        #     response.set_cookie(key=COOKIE_NAME, value=access_token, httponly=True)
        #     return user

    else:
        id_user = UUID(payload["sub"])
    return await get_user_by_id(session=session, id_user=id_user)


async def user_by_id(
    id_user: Annotated[UUID, Path],
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user_authorization),
) -> Optional[User]:
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
