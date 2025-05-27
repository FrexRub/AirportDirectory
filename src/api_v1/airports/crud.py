from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.engine import Result

from src.models.airport import Airport


async def get_all_airport(session: AsyncSession):
    stmt = select(
        Airport.id,
        Airport.name,
        Airport.address,
        Airport.img_top,
        Airport.short_description,
    )
    result: Result = await session.execute(stmt)
    airoports = result.scalars().all()
