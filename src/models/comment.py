from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import UUID, CheckConstraint, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.airport import Airport
    from src.models.user import User


class AirportComment(Base):
    __table_args__ = (CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),)

    comment_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )

    airport_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("airports.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="airport_comments")
    airport: Mapped["Airport"] = relationship(back_populates="comments")

    def __repr__(self):
        return f"<AirportComment(id={self.id}, airport_id={self.airport_id}, rating={self.rating})>"
