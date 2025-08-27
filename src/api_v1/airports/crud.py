from typing import Any, Optional, Sequence
from uuid import UUID

from geoalchemy2.functions import ST_DistanceSphere, ST_Point
from sqlalchemy import Float, Row, select, func
from sqlalchemy.engine import Result
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import cast

from src.core.exceptions import ExceptDB, NotFindData
from src.models.airport import Airport
from src.models.comment import AirportComment

from .schemas import AirPortOutGeoSchemas


async def get_all_airport(session: AsyncSession) -> list[Row[Any]]:
    """
    Возвращает список с данными аэропортов
    :param session: AsyncSession
        сессия БД
    :return: list[Row[Any]]
    """
    stmt = select(
        Airport.id,
        Airport.name,
        Airport.address,
        Airport.img_top,
        Airport.short_description,
    )
    result: Result = await session.execute(stmt)
    airports: Sequence[Row[Any]] = result.all()
    return list(airports)


async def get_airport(session: AsyncSession, id_airport: UUID) -> Airport:
    """
    Возвращает данные аэропорта по ID
    :param session: AsyncSession
        сессия БД
    :param id_airport: UUID
        ID аэропорта
    :return: Airport
    """
    try:
        airport: Optional[Airport] = await session.get(Airport, id_airport)
    except SQLAlchemyError as exc:
        raise ExceptDB(exc)
    if airport is None:
        raise NotFindData("Airport by id not found")
    else:
        rating_stmt = select(func.avg(AirportComment.rating)).where(AirportComment.airport_id == id_airport)
        rating_result = await session.execute(rating_stmt)
        avg_rating = rating_result.scalar()

        airport.average_rating = float(avg_rating) if avg_rating is not None else 0.0
    return airport


async def get_airports_nearest(
    session: AsyncSession, latitude: float, longitude: float, limit: int
) -> list[AirPortOutGeoSchemas]:
    """
    Поиск ближайших аэропортов от заданной точки, города или аэропорта
    :param session: AsyncSession
        сессия БД
    :param latitude: float
        Широта
    :param longitude: float
        Долгота
    :param limit: int
        количество возвращаемых объектов
    :return: list[AirPortOutGeoSchemas]
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

    result: Result = await session.execute(stmt)

    airports_nearest = list()
    for airport, distance in result:
        if (airport.latitude != latitude) and (airport.longitude != longitude):
            data = AirPortOutGeoSchemas(**airport.__dict__)
            data.distance: float = round(distance / 1000, 2)  # type: ignore
            airports_nearest.append(data)

    return airports_nearest[:limit]
