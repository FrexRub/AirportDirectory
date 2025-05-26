import asyncio
import logging
from pathlib import Path

import pandas as pd


from sqlalchemy import select
from sqlalchemy.engine import Result

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
    logger.info("Start copy data to db")
    folder_path: Path = Path(BASE_DIR / "data")

    df = pd.read_excel(folder_path / FILE_NAME)
    df = df.dropna(how="any")

    all_data = df.to_dict("records")
    print("\nДанные в виде списка словарей:")

    for i_data in all_data:
        for key, val in i_data.items():
            print("column: ", key, " -> ", "data: ", val)

    # async with async_session_maker() as session:
    #     stmt = select(User).filter(User.email == "admin@mycomp.com")
    #     res: Result = await session.execute(stmt)
    #     user: User = res.scalar_one_or_none()
    #     if user is None:
    #         logger.info("Users creation completed")
    #         user_admin: UserCreateSchemas = UserCreateSchemas(
    #             full_name="Петров Иван", email="admin@mycomp.com", password="1qaz!QAZ"
    #         )
    #         admin: User = await create_user(session=session, user_data=user_admin)
    #         admin.is_superuser = True
    #         await session.commit()
    #
    #         user: UserCreateSchemas = UserCreateSchemas(
    #             full_name="Ветлицкий Сергей",
    #             email="user1@mycomp.com",
    #             password="2wsx@WSX",
    #         )
    #         res: User = await create_user(session=session, user_data=user)
    #         logger.info("Users have already been created")
    #     else:
    #         logger.info("Users have already been created")


if __name__ == "__main__":
    asyncio.run(data_from_files_to_db())
