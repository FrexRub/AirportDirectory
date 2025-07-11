"""add data to table citys

Revision ID: bdf939c377bf
Revises: 64c2a98ffef8
Create Date: 2025-07-11 09:52:41.542386

"""

from typing import Sequence, Union
from pathlib import Path

import pandas as pd
from alembic import op
from sqlalchemy import orm
from sqlalchemy import exists, select

from src.models.city import City
from src.core.config import BASE_DIR
from sqlalchemy.engine import Result


# revision identifiers, used by Alembic.
revision: str = "bdf939c377bf"
down_revision: Union[str, None] = "64c2a98ffef8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


FILE_NAME = "city.xlsx"


def data_to_model(i_data: dict[str, str | float]) -> City:
    city: City = City(
        region=i_data["region"],
        city=i_data["city"],
        latitude=i_data["latitude"],
        longitude=i_data["longitude"],
    )
    return city


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    folder_path: Path = Path(BASE_DIR / "data")

    df = pd.read_excel(folder_path / FILE_NAME, engine="openpyxl", keep_default_na=False)
    df = df.dropna(how="any")

    all_data: list[dict[str, any]] = df.to_dict("records")  # Данные в виде списка словарей

    for i_data in all_data:
        stmt = select(exists().where(City.city == i_data["city"]))
        res: Result = session.execute(stmt)
        exist: bool = res.scalar()

        if not exist:
            city: City = data_to_model(i_data)
            session.add(city)

    session.commit()


def downgrade() -> None:
    """Downgrade schema."""
    pass
