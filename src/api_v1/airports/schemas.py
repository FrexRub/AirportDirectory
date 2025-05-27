from uuid import uuid4
from pydantic import BaseModel, computed_field, Field, UUID4
from pathlib import Path

from src.core.config import DIR_LOGOTIP, DIR_FOTO


class GeoDataSchemas(BaseModel):
    latitude: float
    longitude: float


class AirPortOutShortSchemas(BaseModel):
    id: UUID4 = Field(default_factory=uuid4)
    name: str
    address: str
    short_description: str
    img_top: str = Field(description="Имя файла логотипа аэропорта")

    @computed_field(description="Полный URL изображения")
    @property
    def image_url(self) -> str:
        file_name: Path = Path(DIR_LOGOTIP / self.img_top)
        return str(file_name)
