import asyncio

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.city import City


async def test_db_operation(test_db_city: AsyncSession):
    """Тест, проверяющий работу с данными из БД."""
    stmt = select(func.count(City.id))
    res: Result = await test_db_city.execute(stmt)
    count = res.scalar()
    assert count == 8, "Данные не загрузились в БД"


async def test_city_get_by_name(
    event_loop: asyncio.AbstractEventLoop,
    client: AsyncClient,
    test_db_city: AsyncSession,
):

    data = {"title": "Адлер"}
    response = await client.get("api/city", params=data)
    assert response.status_code == 200
    assert response.json()["city"] == "Адлер"
