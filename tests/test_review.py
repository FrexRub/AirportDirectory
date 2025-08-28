import asyncio

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.comment import AirportComment
from src.models.airport import Airport


async def test_create_reviews_email_confirmed(
    event_loop: asyncio.AbstractEventLoop,
    client: AsyncClient,
    test_db: AsyncSession,
    token_admin: str,
):
    stmt = select(Airport).filter(Airport.name == "Шереметьево")
    result = await test_db.execute(stmt)
    airport = result.scalars().one_or_none()

    data = {"content": "Всё отлично", "rating": 5, "airport_id": str(airport.id)}
    header = {"Authorization": f"Bearer {token_admin}"}
    response = await client.post(
        "api/reviews",
        json=data,
        headers=header,
    )
    assert response.status_code == 201


async def test_create_reviews_email_unconfirmed(
    event_loop: asyncio.AbstractEventLoop,
    client: AsyncClient,
    test_db: AsyncSession,
    token_user: str,
):
    stmt = select(Airport).filter(Airport.name == "Шереметьево")
    result = await test_db.execute(stmt)
    airport = result.scalars().one_or_none()

    data = {"content": "Всё отлично", "rating": 5, "airport_id": str(airport.id)}
    header = {"Authorization": f"Bearer {token_user}"}
    response = await client.post(
        "api/reviews",
        json=data,
        headers=header,
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Необходимо подтвердить почту"}


async def test_create_reviews_bad_rating(
    event_loop: asyncio.AbstractEventLoop,
    client: AsyncClient,
    test_db: AsyncSession,
    token_admin: str,
):
    stmt = select(Airport).filter(Airport.name == "Шереметьево")
    result = await test_db.execute(stmt)
    airport = result.scalars().one_or_none()

    data = {"content": "Всё отлично", "rating": 10, "airport_id": str(airport.id)}
    header = {"Authorization": f"Bearer {token_admin}"}
    response = await client.post(
        "api/reviews",
        json=data,
        headers=header,
    )
    detail = response.json()["detail"]
    print("------>", detail)
    assert response.status_code == 422
    assert detail[0]["msg"] == "Input should be less than or equal to 5"
