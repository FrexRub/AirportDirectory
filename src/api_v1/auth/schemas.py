from pydantic import BaseModel


class LoginSchemas(BaseModel):
    email: str
    password: str


class AuthUserSchemas(BaseModel):
    name: str
    email: str
    picture: str


class GoogleCallbackSchemas(BaseModel):
    code: str
    state: str


class YandexCallbackSchemas(BaseModel):
    code: str
    state: str
