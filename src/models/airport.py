from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.comment import AirportComment


class Airport(Base):
    name: Mapped[str]
    full_name: Mapped[str]
    city: Mapped[str] = mapped_column(String, index=True)
    address: Mapped[str]
    url: Mapped[str]
    short_description: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    icao: Mapped[str] = mapped_column(String(4))
    iata: Mapped[str] = mapped_column(String(4))
    internal_code: Mapped[str] = mapped_column(String(4))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    geo: Mapped[Geometry] = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    img_top: Mapped[str]
    img_airport: Mapped[str]
    time_zone: Mapped[str]
    online_tablo: Mapped[str]

    comments: Mapped[list["AirportComment"]] = relationship(back_populates="airport", cascade="all, delete-orphan")

    @property
    def average_rating(self) -> Optional[float]:
        if not self.comments:
            return None
        return sum(comment.rating for comment in self.comments) / len(self.comments)
