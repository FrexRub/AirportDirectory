import logging

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.airports.crud import get_airport
from src.api_v1.comments.crude import add_new_comment
from src.api_v1.comments.schemas import CommentAddSchemas, ResultBaseSchemas
from src.core.config import configure_logging
from src.core.database import get_async_session
from src.core.depends import current_user_authorization
from src.core.exceptions import ErrorInData, ExceptDB, NotFindData
from src.models.airport import Airport
from src.models.user import User

router = APIRouter(prefix="/comments", tags=["Comments"])

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/add", response_model=ResultBaseSchemas, status_code=status.HTTP_200_OK)
async def add_comment(
    comment: CommentAddSchemas,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user_authorization),
) -> ResultBaseSchemas:
    """
    Написание комментария об аэропорте
    """
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо подтвердить почту",
        )

    try:
        airport: Airport = await get_airport(session=session, id_airport=comment.airport_id)
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

    try:
        await add_new_comment(session=session, comment=comment, user=user, airport=airport)
    except ErrorInData as exp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{exp}",
        )
    except ExceptDB as exp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{exp}",
        )

    return ResultBaseSchemas(result="Ok")
