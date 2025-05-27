import asyncio
import logging
from pathlib import Path

import pandas as pd

from sqlalchemy import select, exists
from sqlalchemy.engine import Result
from geoalchemy2.functions import ST_Point

from src.core.database import async_session_maker
from src.models.airport import Airport
from src.core.config import configure_logging, BASE_DIR

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)

DIR_NAME = BASE_DIR / "data"
FILE_NAME = "air_bd.xlsx"


async def data_from_files_to_db() -> None:
    """
    Утилита добавления данных в бд
    """
    logger.info("Start add data to db")
    folder_path: Path = Path(BASE_DIR / "data")

    df = pd.read_excel(folder_path / FILE_NAME)
    df = df.dropna(how="any")

    all_data: list[dict[str, any]] = df.to_dict(
        "records"
    )  # Данные в виде списка словарей

    async with async_session_maker() as session:
        for i_data in all_data:
            stmt = select(exists().where(Airport.name == i_data["name"]))
            res: Result = await session.execute(stmt)
            exist: bool = res.scalar()

            if not exist:
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
                session.add(airport)
                logger.info("Airport named %s added to the database" % i_data["name"])
            else:
                logger.info(
                    "The airport named %s is already in the database" % i_data["name"]
                )
        await session.commit()


if __name__ == "__main__":
    asyncio.run(data_from_files_to_db())
