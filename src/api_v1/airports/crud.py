from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.engine import Result

from src.models.airport import Airport


async def get_all_airport(session: AsyncSession):
    stmt = select(Airport)
    result: Result = await session.execute(stmt)
    airports = result.scalars().all()
    return list(airports)
