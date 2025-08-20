from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.comments.schemas import CommentAddSchemas
from src.core.exceptions import ErrorInData, ExceptDB
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
