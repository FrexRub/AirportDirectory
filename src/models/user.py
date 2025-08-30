from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.comment import AirportComment


class User(Base):
    full_name: Mapped[Optional[str]]
    email: Mapped[str] = mapped_column(unique=True, index=True)
    registered_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=datetime.utcnow,
    )
    hashed_password: Mapped[str] = mapped_column(String, nullable=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    airport_comments: Mapped[list["AirportComment"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, username={self.full_name!r})"

    def repr(self) -> str:
        return str(self)
