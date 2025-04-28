from typing import Optional
from datetime import datetime
from uuid import uuid4
import re

from pydantic import (
    BaseModel,
    EmailStr,
    ConfigDict,
    Field,
    field_validator,
    field_serializer,
    UUID4,
)

PATTERN_PASSWORD = (
    r'^(?=.*?[a-z])(?=.*?[A-Z])(?=.*?[0-9])(?=.*?[!"#\$%&\(\)\*\+,-\.\/:;<=>\?@[\]\^_'
    r"`\{\|}~])[a-zA-Z0-9!\$%&\(\)\*\+,-\.\/:;<=>\?@[\]\^_`\{\|}~]{8,}$"
)


class UserBaseSchemas(BaseModel):
    full_name: str
    email: EmailStr


class UserUpdateSchemas(UserBaseSchemas):
    pass


class UserUpdatePartialSchemas(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserCreateSchemas(UserBaseSchemas):
    hashed_password: str = Field(alias="password")

    @field_validator("hashed_password")
    def validate_password(cls, value):
        if not re.match(PATTERN_PASSWORD, value):
            raise ValueError("Invalid password")
        return value


class OutUserSchemas(UserBaseSchemas):
    registered_at: datetime
    id: UUID4 = Field(default_factory=uuid4)

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("registered_at")
    def serialize_registered_at(self, dt: datetime, _info):
        return dt.strftime("%d-%b-%Y")


class LoginSchemas(BaseModel):
    username: str
    password: str
