import asyncio

from httpx import AsyncClient

from src.models.user import User

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


async def test_authorization_user(event_loop: asyncio.AbstractEventLoop, client: AsyncClient, test_user_admin: User):
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


async def test_user_about_me(
    event_loop: asyncio.AbstractEventLoop,
    client: AsyncClient,
    token_admin: str,
):
    header = {"Authorization": f"Bearer {token_admin}"}
    response = await client.get(
        "api/users/me",
        headers=header,
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "TestUser"
