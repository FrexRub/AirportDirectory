import asyncio

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.airport import Airport


async def test_db_operation(test_db: AsyncSession):
    """Тест, проверяющий работу с данными из БД."""
    stmt = select(func.count(Airport.id))
    res: Result = await test_db.execute(stmt)
    count = res.scalar()
    assert count == 8, "Данные не загрузились в БД"


async def test_airport_get_all(
    event_loop: asyncio.AbstractEventLoop,
    client: AsyncClient,
    test_db: AsyncSession,
):
    response = await client.get(
        "api/airports?page=1&size=6",
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 6


async def test_airport_get_detail(
    event_loop: asyncio.AbstractEventLoop,
    client: AsyncClient,
    test_db: AsyncSession,
):
    stmt = select(Airport).filter(Airport.name == "Шереметьево")
    result = await test_db.execute(stmt)
    airport = result.scalars().one_or_none()

    data = {"id": airport.id}
    response = await client.get("api/airport", params=data)
    assert response.status_code == 200
    assert response.json()["name"] == "Шереметьево"


async def test_airport_distance(
    event_loop: asyncio.AbstractEventLoop,
    client: AsyncClient,
    test_db: AsyncSession,
):
    stmt = select(Airport).filter(Airport.name == "Шереметьево")
    result = await test_db.execute(stmt)
    airport = result.scalars().one_or_none()

    data = {
        "latitude_city": 55.75,
        "longitude_city": 37.62,
        "latitude_airport": airport.latitude,
        "longitude_airport": airport.longitude,
    }
    response = await client.get("api/distance", params=data)
    assert response.status_code == 200
    assert response.json()["distance_kilometers"] == 27.2


async def test_airport_nearest(
    event_loop: asyncio.AbstractEventLoop,
    client: AsyncClient,
    test_db: AsyncSession,
):
    data = {
        "latitude": 55.75,
        "longitude": 37.62,
        "limit": 3,
    }
    response = await client.get("api/nearest", params=data)
    print(response.json())
    assert response.status_code == 200
    assert len(response.json()) == 3
    assert response.json()[0]["city"] == "Москва"


async def test_airport_geo_local(
    event_loop: asyncio.AbstractEventLoop,
    client: AsyncClient,
    test_db: AsyncSession,
):
    data = {
        "latitude": 55.75,
        "longitude": 37.62,
    }
    response = await client.get("api/geo-local", params=data)
    print(response.json())
    assert response.status_code == 200
    assert response.json()["city"] == "Москва"
