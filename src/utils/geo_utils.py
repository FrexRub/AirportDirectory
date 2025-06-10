import asyncio
from typing import Optional

from geopy.geocoders import Nominatim  # type: ignore[import-untyped]


async def get_location_info(lat: float, lon: float) -> Optional[dict[str, str]]:
    """
        получение информации гео-данным
    Args:
        lat (float): широта
        lon (float): долгота

    Returns:
        dict[str, str]: информация в виде
    {
    'city': 'Москва',
    'state': 'Москва',
    'country': 'Россия',
    'postcode': '109012',
    'full_address': 'Московский Кремль и Красная Площадь,Москва, Центральный федеральный округ, 109012, Россия'
    }

    """
    geolocator = Nominatim(user_agent="geo_locator")
    location = geolocator.reverse(f"{lat}, {lon}", exactly_one=True)

    await asyncio.sleep(0)

    if location:
        address = location.raw.get("address", {})
        return {
            "city": address.get("city", address.get("town", address.get("village"))),
            "state": address.get("state"),
            "country": address.get("country"),
            "postcode": address.get("postcode"),
            "full_address": location.address,
        }
    return None
