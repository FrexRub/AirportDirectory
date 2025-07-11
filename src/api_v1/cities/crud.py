from typing import Optional

from sqlalchemy import select
from sqlalchemy.engine import Result
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ExceptDB, NotFindData
from src.models.city import City


async def get_city_by_name(session: AsyncSession, title: str) -> City:
    """
    Возвращает данные города по названию
    :param session: AsyncSession
        сессия БД
    :param title: str
        названию города
    :return: City
    """
    try:
        stmt = select(City).filter(City.city == title)
        result: Result = await session.execute(stmt)
        city: Optional[City] = result.scalars().one_or_none()
    except SQLAlchemyError as exc:
        raise ExceptDB(exc)
    if city is None:
        raise NotFindData("City by id not found")
    return city
