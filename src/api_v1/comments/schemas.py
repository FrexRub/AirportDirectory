from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import UUID4, BaseModel, Field, field_serializer


class UserInfoSchemas(BaseModel):
    full_name: Optional[str] = None


class CommentAddSchemas(BaseModel):
    content: str
    rating: int = Field(ge=1, le=5, description="Оценка от 1 до 5")
    airport_id: UUID4 = Field(default_factory=uuid4)


class CommentAllOutSchemas(BaseModel):
    comment_text: str
    rating: int
    created_at: datetime
    user: UserInfoSchemas

    @field_serializer("created_at")
    def serialize_date_of_issue(self, dt: datetime, _info):
        return dt.strftime("%d-%b-%Y")

    class Config:
        from_attributes = True


class CommentAverageRating(BaseModel):
    average_rating: float = Field(default=0.0)
