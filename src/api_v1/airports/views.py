from fastapi import APIRouter, Depends, status

from .schemas import GeoDataSchemas
from src.utils.geo_utils import get_location_info

airports = [
    {
        "id": 1,
        "name": "Шереметьево (Москва)",
        "address": "Московская обл., Химки, Международное шоссе, 1",
        "description": 'Крупнейший международный аэропорт России, главный хаб "Аэрофлота".',
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Sheremetyevo_International_Airport_Terminal_B.jpg/1200px-Sheremetyevo_International_Airport_Terminal_B.jpg",
        "icao": "UUEE",
        "passengers": "40,1 млн",
        "latitude": 55.972642,
        "longitude": 37.414589,
    },
    {
        "id": 2,
        "name": "Домодедово (Москва)",
        "address": "Московская обл., Домодедово, Аэропорт",
        "description": "Один из трёх основных аэропортов Москвы, обслуживает множество международных рейсов.",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Domodedovo_Airport_Terminal.jpg/1200px-Domodedovo_Airport_Terminal.jpg",
        "icao": "UUDD",
        "passengers": "28,2 млн",
        "latitude": 55.972642,
        "longitude": 37.414589,
    },
    {
        "id": 3,
        "name": "Пулково (Санкт-Петербург)",
        "address": "г. Санкт-Петербург, шоссе Пулковское, 41 лит. ЗА",
        "description": "Крупнейший аэропорт Северо-Запада России, важный транспортный узел.",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Pulkovo_Airport_Terminal_1.jpg/1200px-Pulkovo_Airport_Terminal_1.jpg",
        "icao": "ULLI",
        "passengers": "18,1 млн",
        "latitude": 55.972642,
        "longitude": 37.414589,
    },
    {
        "id": 4,
        "name": "Сочи (Адлер)",
        "address": "Краснодарский край, Адлерский р-н, ул. Мира, 50",
        "description": "Главный аэропорт черноморского побережья России, важный курортный хаб.",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Sochi_Airport_2014-02-08.jpg/1200px-Sochi_Airport_2014-02-08.jpg",
        "icao": "URSS",
        "passengers": "6,8 млн",
        "latitude": 55.972642,
        "longitude": 37.414589,
    },
    {
        "id": 5,
        "name": "Кольцово (Екатеринбург)",
        "address": "Свердловская обл., г. Екатеринбург, ул. Бахчиванджи, 1",
        "description": "Крупнейший аэропорт Урала, важный транспортный узел между Европой и Азией.",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Koltsovo_Airport_Terminal.jpg/1200px-Koltsovo_Airport_Terminal.jpg",
        "icao": "USSS",
        "passengers": "6,2 млн",
        "latitude": 55.972642,
        "longitude": 37.414589,
    },
    {
        "id": 6,
        "name": "Толмачёво (Новосибирск)",
        "address": "Новосибирская обл., г. Новосибирск, аэропорт Толмачёво",
        "description": "Крупнейший аэропорт Сибири, важный хаб для транзитных рейсов.",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Tolmachevo_Airport_Terminal.jpg/1200px-Tolmachevo_Airport_Terminal.jpg",
        "icao": "UNNT",
        "passengers": "5,9 млн",
        "latitude": 55.972642,
        "longitude": 37.414589,
    },
]

router = APIRouter(tags=["Airports"])


@router.get("/airport")
def get_airports_all():
    return airports


@router.post("/geo-local")
async def get_city_name(geo_data: GeoDataSchemas):
    city_info = get_location_info(geo_data.latitude, geo_data.longitude)

    if city_info:
        return {"city": city_info["city"]}
    else:
        return {"city": "Неизвестный город"}
