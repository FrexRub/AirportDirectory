import os
from typing import Optional
from uuid import uuid4

from pydantic import UUID4, BaseModel, Field, computed_field

from src.core.config import DIR_FOTO, DIR_LOGOTIP


class GeoDataSchemas(BaseModel):
    latitude: float
    longitude: float


class AirPortOutShortSchemas(BaseModel):
    id: UUID4 = Field(default_factory=uuid4)
    name: str
    address: str
    short_description: str
    img_top: str = Field(description="Имя файла логотипа аэропорта")


class AirPortOutAllSchemas(BaseModel):
    id: UUID4 = Field(default_factory=uuid4)
    name: str
    full_name: str
    city: str
    address: str
    url: str
    short_description: str
    description: str
    icao: str
    iata: str
    internal_code: str
    latitude: float
    longitude: float
    img_top: str = Field(description="Имя файла логотипа аэропорта")
    img_airport: str = Field(description="Имя файла фотографии аэропорта")
    time_zone: str
    online_tablo: str

    @property
    @computed_field(description="Полный URL изображения логотипа")
    def image_url(self) -> str:
        file_name: str = os.path.join(DIR_LOGOTIP, self.img_top)
        return file_name

    class Config:
        from_attributes = True

    @property
    @computed_field(description="Полный URL фото аэропорта")
    def image_foto_url(self) -> str:
        file_name: str = os.path.join(DIR_FOTO, self.img_top)
        return file_name


class AirPortOutGeoSchemas(BaseModel):
    id: UUID4 = Field(default_factory=uuid4)
    name: str
    city: str
    latitude: float
    longitude: float
    img_top: str
    distance: Optional[float] = Field(None, description="Distance in meters")
