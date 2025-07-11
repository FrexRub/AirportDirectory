import asyncio
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import exists, select
from sqlalchemy.engine import Result

from src.core.config import BASE_DIR, configure_logging
from src.core.database import async_session_maker
from src.models.city import City

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)

DIR_NAME = BASE_DIR / "data"
FILE_NAME = "city.xlsx"


async def data_to_model(i_data: dict[str, str | float]) -> City:
    city: City = City(
        region=i_data["region"],
        city=i_data["city"],
        latitude=i_data["latitude"],
        longitude=i_data["longitude"],
    )
    return city


async def city_from_files_to_db() -> None:
    """
    Утилита добавления данных в бд
    """
    logger.info("Start add city to db")
    folder_path: Path = Path(BASE_DIR / "data")

    df = pd.read_excel(folder_path / FILE_NAME, engine="openpyxl", keep_default_na=False)
    df = df.dropna(how="any")

    all_data: list[dict[str, any]] = df.to_dict("records")  # Данные в виде списка словарей

    async with async_session_maker() as session:
        for i_data in all_data:
            stmt = select(exists().where(City.city == i_data["city"]))
            res: Result = await session.execute(stmt)
            exist: bool = res.scalar()

            if not exist:
                city: City = await data_to_model(i_data)
                session.add(city)
                logger.info("City named %s added to the database" % i_data["city"])
            else:
                logger.info("The city %s is already in the database" % i_data["city"])
        await session.commit()


if __name__ == "__main__":
    asyncio.run(city_from_files_to_db())
