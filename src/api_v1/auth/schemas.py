from pydantic import BaseModel


class LoginSchemas(BaseModel):
    email: str
    password: str
