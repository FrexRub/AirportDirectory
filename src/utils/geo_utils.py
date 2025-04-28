from geopy.geocoders import Nominatim


def get_location_info(lat: float, lon: float):
    """
        получение информации гео-данным
    Args:
        lat (float): ширина
        lon (float): долгота

    Returns:
        dict[str, str]: информация в виде
    {
    'city': 'Москва',
    'state': 'Москва',
    'country': 'Россия',
    'postcode': '109012',
    'full_address': 'Московский Кремль и Красная Площадь, Хрустальный переулок, 15, Китай-город, Тверской район, Москва, Центральный федеральный округ, 109012, Россия'
    }

    """
    geolocator = Nominatim(user_agent="geo_locator")
    location = geolocator.reverse(f"{lat}, {lon}", exactly_one=True)

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
