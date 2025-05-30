from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.engine import Result
from geoalchemy2.functions import ST_Point, ST_DistanceSphere

from src.models.airport import Airport


async def get_all_airport(session: AsyncSession) -> Sequence[Airport]:
    stmt = select(Airport)
    result: Result = await session.execute(stmt)
    airports: Sequence[Airport] = result.scalars().all()
    return airports


async def get_airports_nearest(
    session: AsyncSession,
    latitude_city: float,
    longitude_city: float,
) -> Sequence[Airport]:
    geo_city = ST_Point(longitude_city, latitude_city, srid=4326)
    stmt = select(Airport).order_by(ST_DistanceSphere(geo_city, Airport.geo)).limit(5)
    result: Result = await session.execute(stmt)
    airports: Sequence[Airport] = result.scalars().all()
    return airports
