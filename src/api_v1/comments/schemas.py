from uuid import uuid4

from pydantic import UUID4, BaseModel, Field


class ResultBaseSchemas(BaseModel):
    result: str


class CommentAddSchemas(BaseModel):
    content: str
    rating: int = Field(ge=1, le=5, description="Оценка от 1 до 5")
    airport_id: UUID4 = Field(default_factory=uuid4)
