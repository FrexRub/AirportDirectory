import logging

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.cities.crud import get_city_by_name
from src.core.config import CACHE_EXP, configure_logging
from src.core.database import get_async_session, get_cache_connection
from src.core.exceptions import ExceptDB, NotFindData
from src.models.city import City
from src.utils.data_utils import json_to_model, model_to_json

from .schemas import CityDataSchemas

router = APIRouter(tags=["Cities"])

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


@router.get("/city", response_model=CityDataSchemas)
async def get_city(
    title: str,
    session: AsyncSession = Depends(get_async_session),
    db_cache=Depends(get_cache_connection),
) -> CityDataSchemas:
    """
    Возвращает данные города по его названию
    """
    logger.info("Start request get city by name %s", title)
    city_json: str = await db_cache.get(str(title))
    if city_json is None:
        try:
            city_obj: City = await get_city_by_name(session=session, title=title)
            city: CityDataSchemas = CityDataSchemas(**city_obj.__dict__)
        except ExceptDB as exp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{exp}",
            )
        except NotFindData as exp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{exp}",
            )
        else:
            city_json_model: str = await model_to_json(pydantic_model=CityDataSchemas, object=city_obj)
            await db_cache.set(str(title), city_json_model, ex=CACHE_EXP)
            logger.info("Write in cache info about city with id %s", title)
    else:
        logger.info("Read from cache info about city with id %s", title)
        city: CityDataSchemas = await json_to_model(  # type: ignore
            pydantic_model=CityDataSchemas, json_object=city_json
        )  # type: ignore
    return city
