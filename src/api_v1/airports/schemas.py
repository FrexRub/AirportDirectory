from pydantic import BaseModel


class GeoDataSchemas(BaseModel):
    latitude: float
    longitude: float
