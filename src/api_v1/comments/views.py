import logging
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.airports.crud import get_airport
from src.api_v1.comments.crude import add_new_comment, get_comment
from src.api_v1.comments.schemas import CommentAddSchemas, CommentAllOutSchemas
from src.core.config import configure_logging
from src.core.database import get_async_session
from src.core.depends import current_user_authorization
from src.core.exceptions import ErrorInData, ExceptDB, NotFindData
from src.models.airport import Airport
from src.models.user import User

router = APIRouter(prefix="/comments", tags=["Comments"])

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/add", status_code=status.HTTP_201_CREATED)
async def add_comment(
    comment: CommentAddSchemas,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user_authorization),
):
    """
    Написание комментария об аэропорте
    """
    logger.info("Start add comment user by id %s" % user.id)
    if not user.is_verified:
        logger.warning("The user's email with the id %s has not been confirmed" % user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо подтвердить почту",
        )

    try:
        logger.info("The beginning of the aeroport search by id %s" % user.id)
        airport: Airport = await get_airport(session=session, id_airport=comment.airport_id)
    except ExceptDB as exp:
        logger.error(exp)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{exp}",
        )
    except NotFindData as exp:
        logger.error(exp)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{exp}",
        )

    try:
        logger.info("Adding a comment about an airport with an id %s" % comment.airport_id)
        await add_new_comment(session=session, comment=comment, user=user, airport=airport)
    except ErrorInData as exp:
        logger.error(exp)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{exp}",
        )
    except ExceptDB as exp:
        logger.error(exp)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{exp}",
        )


@router.get("/comments", response_model=list[CommentAllOutSchemas])
async def get_comments_airport(
    id: UUID,
    session: AsyncSession = Depends(get_async_session),
) -> list[CommentAllOutSchemas]:
    logger.info("Getting comments about an airport with an id")
    try:
        comments: list[CommentAllOutSchemas] = await get_comment(session=session, id_airport=id)
    except ExceptDB as exp:
        logger.error(exp)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{exp}",
        )
    except NotFindData as exp:
        logger.error(exp)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{exp}",
        )

    return comments
