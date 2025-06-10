from httpx import AsyncClient

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.engine import Result
import asyncio

from src.models.user import User
from src.core.config import COOKIE_NAME

username = "Bob"
email = "Bob@mail.ru"
password = "1qaz!QAZ"


async def test_register(
    event_loop: asyncio.AbstractEventLoop,
    client: AsyncClient,
):
    user = {
        "username": username,
        "email": email,
        "password": password,
    }
    response = await client.post("/api/users/register", json=user)
    assert response.status_code == 201
    assert response.json()["user"]["full_name"] == username


async def test_authorization_user(
    event_loop: asyncio.AbstractEventLoop, client: AsyncClient, test_user_admin: User
):
    response = await client.post(
        "/api/users/login",
        json={"username": "testuser@example.com", "password": "1qaz!QAZ"},
    )

    assert response.status_code == 202
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


async def test_user_unique_email(
    event_loop: asyncio.AbstractEventLoop,
    client: AsyncClient,
    test_user: User,
):
    user = {
        "username": username,
        "email": "petr@mail.com",
        "password": password,
    }
    response = await client.post("/api/users/register", json=user)
    assert response.json() == {"detail": "The email address is already in use"}
    assert response.status_code == 400


async def test_user_bad_password(
    event_loop: asyncio.AbstractEventLoop,
    client: AsyncClient,
    test_user: User,
):
    user = {
        "username": username,
        "email": email,
        "password": "123",
    }
    response = await client.post("/api/users/register", json=user)
    assert response.json()["detail"][0]["msg"] == "Value error, Invalid password"
    assert response.status_code == 422


#
#
# async def test_user_put(
#     event_loop: asyncio.AbstractEventLoop,
#     client: AsyncClient,
#     token_admin: str,
#     db_session: AsyncSession,
# ):
#     stmt = select(User).filter(User.email == email)
#     res: Result = await db_session.execute(stmt)
#     user_db: User | None = res.scalar_one_or_none()
#     user_id: str = str(user_db.id)
#
#     user = {"username": "Lena", "email": "smirnova@mail.ru"}
#     cookies = {COOKIE_NAME: token_admin}
#
#     response = await client.put(
#         f"/api/users/{user_id}/",
#         json=user,
#         cookies=cookies,
#     )
#
#     stmt = select(User).filter(User.email == "smirnova@mail.ru")
#     res: Result = await db_session.execute(stmt)
#     user_db: User | None = res.scalar_one_or_none()
#
#     assert response.status_code == 200
#     assert response.json()["username"] == "Lena"
#     assert response.json()["email"] == "smirnova@mail.ru"
#     assert user_db.email == "smirnova@mail.ru"
#
#
