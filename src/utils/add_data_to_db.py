import asyncio
import logging
from pathlib import Path

import pandas as pd
from geoalchemy2.functions import ST_Point
from sqlalchemy import exists, select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import BASE_DIR, configure_logging
from src.core.database import async_session_maker
from src.models.airport import Airport

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)

DIR_NAME = BASE_DIR / "data"
FILE_NAME = "air_bd.xlsx"


async def data_to_model(i_data: dict[str, str | float]) -> Airport:
    airport: Airport = Airport(
        name=i_data["name"],
        full_name=i_data["full_name"],
        city=i_data["city"],
        address=i_data["address"],
        url=i_data["url"],
        short_description=i_data["short_description"],
        description=i_data["description"],
        icao=i_data["icao"],
        iata=i_data["iata"],
        internal_code=i_data["internal_code"],
        latitude=i_data["latitude"],
        longitude=i_data["longitude"],
        geo=ST_Point(i_data["longitude"], i_data["latitude"], srid=4326),
        img_top=i_data["img_top"],
        img_airport=i_data["img_airport"],
        time_zone=i_data["time_zone"],
        online_tablo=i_data["online_tablo"],
    )
    return airport


async def data_from_files_to_db() -> None:
    """
    Утилита добавления данных в бд
    """
    logger.info("Start add data to db")
    folder_path: Path = Path(BASE_DIR / "data")

    df = pd.read_excel(folder_path / FILE_NAME, engine="openpyxl", keep_default_na=False)
    df = df.dropna(how="any")

    all_data: list[dict[str, any]] = df.to_dict("records")  # Данные в виде списка словарей

    async with async_session_maker() as session:
        for i_data in all_data:
            stmt = select(exists().where(Airport.name == i_data["name"]))
            res: Result = await session.execute(stmt)
            exist: bool = res.scalar()

            if not exist:
                airport: Airport = await data_to_model(i_data)
                session.add(airport)
                logger.info("Airport named %s added to the database" % i_data["name"])
            else:
                logger.info("The airport named %s is already in the database" % i_data["name"])
        await session.commit()


async def data_from_files_to_test_db(session: AsyncSession) -> None:
    """
    Утилита добавления данных в тестовую бд
    """
    logger.info("Start add data to test db")
    folder_path: Path = Path(BASE_DIR / "data")

    df = pd.read_excel(folder_path / FILE_NAME)
    df = df.dropna(how="any")

    first_eight_records = df.head(8)

    all_data: list[dict[str, any]] = first_eight_records.to_dict("records")

    for i_data in all_data:
        airport: Airport = await data_to_model(i_data)
        session.add(airport)

    await session.commit()


if __name__ == "__main__":
    asyncio.run(data_from_files_to_db())
