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
                    Airport.geo,  # Assuming Airport has 'geo' column of geometry type
                ),
                Float,
            ).label("distance"),
        )
        .order_by("distance")
        .limit(limit)
    )

    # stmt = select(Airport).order_by(ST_DistanceSphere(geo, Airport.geo)).limit(limit)
    result: Result = await session.execute(stmt)
    # airports: Sequence[Airport] = result.scalars().all()

    airports_nearest = list()
    for airport, distance in result:
        print(airport, distance)
        # data = AirPortOutGeoSchemas.model_validate(airport)
        # data.distance = distance
        # airports_nearest.append(data)

    return airports_nearest
    # return airports
