from httpx import AsyncClient

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from sqlalchemy.engine import Result

from src.models.airport import Airport


# async def test_airport_1(
#     event_loop: asyncio.AbstractEventLoop,
#     client: AsyncClient,
#     token_admin: str,
# ):
#     header = {"Authorization": f"Bearer {token_admin}"}
#     response = await client.get(
#         "api/users/me",
#         headers=header,
#     )
#     assert response.status_code == 200
#     assert response.json()["full_name"] == "TestUser"


async def test_db_operation(test_db: AsyncSession):
    """Тест, проверяющий работу с данными из БД."""
    stmt = select(func.count(Airport.id))
    res: Result = await test_db.execute(stmt)
    count = res.scalar()
    assert count == 8, "Данные не загрузились в БД"
