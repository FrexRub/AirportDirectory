from fastapi import HTTPException
from fastapi import status

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


class NotFindUser(Exception):
    pass


class ExceptDB(Exception):
    pass


class ExceptUser(Exception):
    pass


class ErrorInData(Exception):
    pass


class EmailInUse(Exception):
    pass


class UniqueViolationError(Exception):
    pass
