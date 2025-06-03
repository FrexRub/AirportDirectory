from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, Float
from sqlalchemy.engine import Result
from sqlalchemy.sql.expression import cast
from geoalchemy2.functions import ST_Point, ST_DistanceSphere

from src.models.airport import Airport
from .schemas import AirPortOutGeoSchemas


async def get_all_airport(session: AsyncSession) -> Sequence[Airport]:
    stmt = select(Airport)
    result: Result = await session.execute(stmt)
    airports: Sequence[Airport] = result.scalars().all()
    return airports


async def get_airports_nearest(
    session: AsyncSession, latitude: float, longitude: float, limit: int
) -> list[AirPortOutGeoSchemas]:
    """
    Поиск ближайших аэропортов от заданной точки, города или аэропорта
    :param session:
    :param latitude:
    :param longitude:
    :param limit:
    :return:
    """
    geo = ST_Point(longitude, latitude, srid=4326)

    stmt = (
        select(
            Airport,
            cast(
                ST_DistanceSphere(
                    geo,
                    Airport.geo,
                ),
                Float,
            ).label("distance"),
        )
        .order_by("distance")
        .limit(limit + 1)
    )

    # stmt = select(Airport).order_by(ST_DistanceSphere(geo, Airport.geo)).limit(limit)
    # airports: Sequence[Airport] = result.scalars().all()
    result: Result = await session.execute(stmt)

    airports_nearest = list()
    for airport, distance in result:
        if (airport.latitude != latitude) and (airport.longitude != longitude):
            data = AirPortOutGeoSchemas(**airport.__dict__)
            data.distance: float = round(distance / 1000, 2)
            airports_nearest.append(data)

    return airports_nearest[:limit]
