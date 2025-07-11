from sqlalchemy import Float, String, Index
from sqlalchemy.orm import Mapped, mapped_column, validates

from src.models.base import Base


class City(Base):
    __table_args__ = (Index("idx_users_city_hash", "city", postgresql_using="hash"),)
    region: Mapped[str]
    city: Mapped[str] = mapped_column(String)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)

    @validates("latitude")
    def validate_latitude(self, key, longitude):
        return round(longitude, 5)

    @validates("longitude")
    def validate_longitude(self, key, longitude):
        return round(longitude, 5)
