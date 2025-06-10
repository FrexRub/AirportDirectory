import json
import logging
from typing import Any, Union
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.exceptions import HTTPException
from fastapi_pagination import Page, paginate
from geoalchemy2.functions import ST_DistanceSphere, ST_Point
from geoalchemy2.types import Geometry
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.airports.crud import get_airport, get_airports_nearest, get_all_airport
from src.core.config import configure_logging
from src.core.database import get_async_session, get_cache_connection
from src.core.exceptions import ExceptDB, NotFindData
from src.models.airport import Airport
from src.utils.data_utils import json_to_model, model_to_json
from src.utils.geo_utils import get_location_info

from .schemas import AirPortOutAllSchemas, AirPortOutGeoSchemas, AirPortOutShortSchemas

router = APIRouter(tags=["Airports"])

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


@router.get("/airports", response_model=Page[AirPortOutShortSchemas])
async def get_airports_all(
    session: AsyncSession = Depends(get_async_session),
    db_cache=Depends(get_cache_connection),
) -> Page[AirPortOutShortSchemas]:
    """
    Возвращает список с данными аэропортов
    """
    all_airports = await db_cache.lrange("airports", 0, -1)
    if not all_airports:
        airports_db: list[Any] = await get_all_airport(session)
        for airport in airports_db:
            id_, name, address, img_top, short_description = airport
            airport_data = {
                "id": str(id_),
                "name": name,
                "address": address,
                "img_top": img_top,
                "short_description": short_description,
            }
            await db_cache.rpush("airports", json.dumps(airport_data))
        logger.info("Write in cache info about airports")
    else:
        logger.info("Read from cache info about airports")
        airports_db: list[AirPortOutShortSchemas] = list()  # type: ignore
        for airport_json in all_airports:
            airport_dict: dict[str, Any] = json.loads(airport_json)
            airport_dict["id"] = UUID(airport_dict["id"])
            airports_db.append(AirPortOutShortSchemas(**airport_dict))
    return paginate(airports_db)


@router.get("/airport", response_model=AirPortOutAllSchemas)
async def get_airport_by_id(
    id: UUID,
    session: AsyncSession = Depends(get_async_session),
    db_cache=Depends(get_cache_connection),
) -> AirPortOutAllSchemas:
    """
    Возвращает данные аэропорта по ID
    """
    airport_json: str = await db_cache.get(str(id))
    if airport_json is None:
        try:
            airport_obj: Airport = await get_airport(session=session, id_airport=id)
            airport: AirPortOutAllSchemas = AirPortOutAllSchemas(**airport_obj.__dict__)
        except ExceptDB as exp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{exp}",
            )
        except NotFindData as exp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{exp}",
            )
        else:
            airport_json_model: str = await model_to_json(
                pydantic_model=AirPortOutAllSchemas, object=airport_obj
            )
            await db_cache.set(str(id), airport_json_model, ex=3600)
            logger.info("Write in cache info about airport with id %s", str(id))
    else:
        logger.info("Read from cache info about airport with id %s", str(id))
        airport: AirPortOutAllSchemas = await json_to_model(  # type: ignore
            pydantic_model=AirPortOutAllSchemas, json_object=airport_json
        )  # type: ignore
    return airport


@router.get("/distance")
async def get_distance(
    latitude_city: float = Query(..., description="Широта города"),
    longitude_city: float = Query(..., description="Долгота города"),
    latitude_airport: float = Query(..., description="Широта аэропорта"),
    longitude_airport: float = Query(..., description="Долгота аэропорта"),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, float]:
    """
    Возвращает расстояние от города до аэропорта
    """
    geo_city: Union[Geometry, ST_Point] = ST_Point(
        longitude_city, latitude_city, srid=4326
    )
    geo_airport: Union[Geometry, ST_Point] = ST_Point(
        longitude_airport, latitude_airport, srid=4326
    )

    distance: float = await session.scalar(
        select(ST_DistanceSphere(geo_city, geo_airport))
    )  # результат в метрах
    distance_km: float = round(distance / 1000, 2)
    distance_meters: float = round(distance, 2)

    return {"distance_meters": distance_meters, "distance_kilometers": distance_km}


@router.get("/nearest", response_model=list[AirPortOutGeoSchemas])
async def get_nearest_airports(
    latitude: float = Query(..., description="Широта города/аэропорта"),
    longitude: float = Query(..., description="Долгота города/аэропорта"),
    limit: int = 3,
    session: AsyncSession = Depends(get_async_session),
    db_cache=Depends(get_cache_connection),
) -> list[AirPortOutGeoSchemas]:
    """
    Возвращает список ближайших к заданной точке аэропортов
    """
    redis_key: str = f"{longitude}:{latitude}"
    all_airports: list[str] = await db_cache.lrange(redis_key, 0, -1)
    if not all_airports:
        airports_nearest: list[AirPortOutGeoSchemas] = await get_airports_nearest(
            session=session,
            latitude=latitude,
            longitude=longitude,
            limit=limit,
        )
        for airport in airports_nearest:
            await db_cache.rpush(redis_key, airport.model_dump_json())
        logger.info("Write in cache info about airports nearest")
    else:
        logger.info("Read from cache info about airports nearest")
        # all_airports: list[str] = await db_cache.lrange(redis_key, 0, -1)
        airports_nearest: list[AirPortOutGeoSchemas] = list()  # type: ignore
        for airport_json in all_airports:
            airport_dict: dict[str, Any] = json.loads(airport_json)
            obj: AirPortOutGeoSchemas = AirPortOutGeoSchemas(**airport_dict)
            airports_nearest.append(obj)
    return airports_nearest


@router.get("/geo-local")
async def get_city_name(
    latitude: float = Query(..., description="Широта"),
    longitude: float = Query(..., description="Долгота"),
) -> dict[str, str]:
    """
    Возвращает наименование населенного пункта по заданным координатам
    """
    city_info = await get_location_info(latitude, longitude)

    if city_info:
        return {"city": city_info["city"]}
    else:
        return {"city": "Неизвестный город"}
