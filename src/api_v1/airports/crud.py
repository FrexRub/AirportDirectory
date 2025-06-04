from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, Float
from sqlalchemy.engine import Result
from sqlalchemy.sql.expression import cast
from geoalchemy2.functions import ST_Point, ST_DistanceSphere

from src.models.airport import Airport
from .schemas import AirPortOutGeoSchemas
from src.core.exceptions import ExceptDB, NotFindData


async def get_all_airport(session: AsyncSession) -> list[tuple[Any]]:
    stmt = select(
        Airport.id,
        Airport.name,
        Airport.address,
        Airport.img_top,
        Airport.short_description,
    )
    result: Result = await session.execute(stmt)
    airports: list[tuple[Any]] = result.all()
    return airports


async def get_airport(session: AsyncSession, id_airport: UUID) -> Airport:
    try:
        airport: Airport = await session.get(Airport, id_airport)
    except SQLAlchemyError as exc:
        raise ExceptDB(exc)
    if airport is None:
        raise NotFindData("Airport by id not found")
    return airport


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
