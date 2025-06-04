from typing import Sequence, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2.functions import ST_Point, ST_DistanceSphere
from geoalchemy2.types import Geometry


from .schemas import AirPortOutAllSchemas, AirPortOutShortSchemas, AirPortOutGeoSchemas
from src.utils.geo_utils import get_location_info
from src.api_v1.airports.crud import get_all_airport, get_airports_nearest, get_airport
from src.core.database import get_async_session
from src.models.airport import Airport
from src.core.exceptions import ExceptDB, NotFindData


airports = [
    {
        "id": 1,
        "name": "Шереметьево (Москва)",
        "address": "Московская обл., Химки, Международное шоссе, 1",
        "short_description": 'Крупнейший международный аэропорт России, главный хаб "Аэрофлота".',
        "img_top": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Sheremetyevo_International_Airport_Terminal_B.jpg/1200px-Sheremetyevo_International_Airport_Terminal_B.jpg",
        "icao": "UUEE",
        "passengers": "40,1 млн",
        "latitude": 55.972642,
        "longitude": 37.414589,
    },
    {
        "id": 2,
        "name": "Домодедово (Москва)",
        "address": "Московская обл., Домодедово, Аэропорт",
        "short_description": "Один из трёх основных аэропортов Москвы, обслуживает множество международных рейсов.",
        "img_top": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Domodedovo_Airport_Terminal.jpg/1200px-Domodedovo_Airport_Terminal.jpg",
        "icao": "UUDD",
        "passengers": "28,2 млн",
        "latitude": 55.972642,
        "longitude": 37.414589,
    },
    {
        "id": 3,
        "name": "Пулково (Санкт-Петербург)",
        "address": "г. Санкт-Петербург, шоссе Пулковское, 41 лит. ЗА",
        "short_description": "Крупнейший аэропорт Северо-Запада России, важный транспортный узел.",
        "img_top": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Pulkovo_Airport_Terminal_1.jpg/1200px-Pulkovo_Airport_Terminal_1.jpg",
        "icao": "ULLI",
        "passengers": "18,1 млн",
        "latitude": 55.972642,
        "longitude": 37.414589,
    },
    {
        "id": 4,
        "name": "Сочи (Адлер)",
        "address": "Краснодарский край, Адлерский р-н, ул. Мира, 50",
        "short_description": "Главный аэропорт черноморского побережья России, важный курортный хаб.",
        "img_top": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Sochi_Airport_2014-02-08.jpg/1200px-Sochi_Airport_2014-02-08.jpg",
        "icao": "URSS",
        "passengers": "6,8 млн",
        "latitude": 55.972642,
        "longitude": 37.414589,
    },
    {
        "id": 5,
        "name": "Кольцово (Екатеринбург)",
        "address": "Свердловская обл., г. Екатеринбург, ул. Бахчиванджи, 1",
        "short_description": "Крупнейший аэропорт Урала, важный транспортный узел между Европой и Азией.",
        "img_top": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Koltsovo_Airport_Terminal.jpg/1200px-Koltsovo_Airport_Terminal.jpg",
        "icao": "USSS",
        "passengers": "6,2 млн",
        "latitude": 55.972642,
        "longitude": 37.414589,
    },
    {
        "id": 6,
        "name": "Толмачёво (Новосибирск)",
        "address": "Новосибирская обл., г. Новосибирск, аэропорт Толмачёво",
        "short_description": "Крупнейший аэропорт Сибири, важный хаб для транзитных рейсов.",
        "img_top": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Tolmachevo_Airport_Terminal.jpg/1200px-Tolmachevo_Airport_Terminal.jpg",
        "icao": "UNNT",
        "passengers": "5,9 млн",
        "latitude": 55.972642,
        "longitude": 37.414589,
    },
]

router = APIRouter(tags=["Airports"])


@router.get("/airports", response_model=list[AirPortOutShortSchemas])
async def get_airports_all(
    session: AsyncSession = Depends(get_async_session),
) -> list[AirPortOutShortSchemas]:
    airports_db: list[tuple[Any]] = await get_all_airport(session)
    return airports_db


@router.get("/airport", response_model=AirPortOutAllSchemas)
async def get_airport_by_id(
    id: UUID,
    session: AsyncSession = Depends(get_async_session),
) -> Sequence[Airport]:
    try:
        airport = await get_airport(session=session, id_airport=id)
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
    return airport


@router.get("/distance")
async def get_distance(
    latitude_city: float = Query(..., description="Широта города"),
    longitude_city: float = Query(..., description="Долгота города"),
    latitude_airport: float = Query(..., description="Широта аэропорта"),
    longitude_airport: float = Query(..., description="Долгота аэропорта"),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, float]:
    geo_city: Geometry = ST_Point(longitude_city, latitude_city, srid=4326)
    geo_airport: Geometry = ST_Point(longitude_airport, latitude_airport, srid=4326)

    distance: float = await session.scalar(
        select(ST_DistanceSphere(geo_city, geo_airport))
    )  # результат в метрах
    distance_km: float = round(distance / 1000, 2)
    distance_meters: float = round(distance, 2)

    return {"distance_meters": distance_meters, "distance_kilometers": distance_km}


@router.get("/nearest", response_model=list[AirPortOutGeoSchemas])
async def get_nearest_airports(
    latitude: float = Query(..., description="Широта"),
    longitude: float = Query(..., description="Долгота"),
    limit: int = 3,
    session: AsyncSession = Depends(get_async_session),
) -> Sequence[Airport]:
    airports_nearest: list[AirPortOutGeoSchemas] = await get_airports_nearest(
        session=session,
        latitude=latitude,
        longitude=longitude,
        limit=limit,
    )
    return airports_nearest


@router.get("/geo-local")
async def get_city_name(
    latitude: float = Query(..., description="Широта"),
    longitude: float = Query(..., description="Долгота"),
):
    city_info = await get_location_info(latitude, longitude)

    if city_info:
        return {"city": city_info["city"]}
    else:
        return {"city": "Неизвестный город"}
