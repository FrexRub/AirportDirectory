from pydantic import BaseModel


class CityDataSchemas(BaseModel):
    city: str
    latitude: float
    longitude: float
