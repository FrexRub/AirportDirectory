from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.engine import Result
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.api_v1.comments.schemas import CommentAddSchemas
from src.core.exceptions import ErrorInData, ExceptDB, NotFindData
from src.models.airport import Airport
from src.models.comment import AirportComment
from src.models.user import User


async def add_new_comment(session: AsyncSession, comment: CommentAddSchemas, user: User, airport: Airport) -> None:
    """
    Добавление нового комментария об аэропорте в БД
    """
    try:
        new_comment: AirportComment = AirportComment(
            comment_text=comment.content, rating=comment.rating, user=user, airport=airport
        )
    except ValueError as exc:
        raise ErrorInData(str(exc))

    try:
        session.add(new_comment)
    except SQLAlchemyError as exc:
        raise ExceptDB(exc)

    await session.commit()


async def get_comment(session: AsyncSession, id_airport: UUID):
    """
    Возвращает комментарии об аэропорте
    """
    try:
        airport: Optional[Airport] = await session.get(Airport, id_airport)
    except SQLAlchemyError as exc:
        raise ExceptDB(exc)
    if airport is None:
        raise NotFindData("Airport by id not found")

    try:
        stmt = (
            select(AirportComment)
            .options(joinedload(AirportComment.user))
            .filter(AirportComment.airport_id == id_airport)
        )
        result: Result = await session.execute(stmt)
        comments = result.scalars().all()
    except SQLAlchemyError as exc:
        raise ExceptDB(exc)

    return comments


async def get_average_rating(session: AsyncSession, id_airport: UUID) -> float:
    """
    Возвращает рейтинг аэропорта по отзывам
    """
    try:
        stmt = select(func.avg(AirportComment.rating)).where(AirportComment.airport_id == id_airport)
        rating_result = await session.execute(stmt)
        avg_rating = rating_result.scalar()
    except SQLAlchemyError as exc:
        raise ExceptDB(exc)

    return float(avg_rating) if avg_rating is not None else 0.0
