import asyncio
import json
from typing import Any, Type, TypeVar

from pydantic import BaseModel

from src.models.base import Base

T = TypeVar("T", bound=BaseModel)


async def model_to_json(pydantic_model: Type[T], object: Base) -> str:
    """
    Преобразовывает объект БД в модель pydantic и затем в json
    :param pydantic_model: Type[T]
        модель pydantic
    :param object: Base
        объект БД
    :return: str
    """
    await asyncio.sleep(0)
    data_json: str = pydantic_model(**object.__dict__).model_dump_json()
    return data_json


async def json_to_model(pydantic_model: Type[T], json_object: str) -> T:
    """
    Преобразовывает json строку с данными объекта в модель pydantic
    :param pydantic_model: Type[T]
        модель pydantic
    :param json_object: str
        json строка с данными объекта
    :return: T
    """
    await asyncio.sleep(0)
    data_dict: dict[str, Any] = json.loads(json_object)
    data_model: T = pydantic_model(**data_dict)
    return data_model
