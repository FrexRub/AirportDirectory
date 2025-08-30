import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.auth.schemas import AuthUserSchemas
from src.api_v1.users.crud import get_user_from_db
from src.core.config import configure_logging
from src.core.exceptions import NotFindUser
from src.models.user import User

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


async def check_auth_user(session: AsyncSession, user_info: AuthUserSchemas) -> User:
    logger.info("Start check user by email %s" % user_info.email)
    try:
        user: User = await get_user_from_db(session=session, email=user_info.email)
    except NotFindUser:
        logger.info("User with email %s is not registered" % user_info.email)
        user: User = User(
            full_name=user_info.name,
            email=user_info.email,
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()
        logger.info("User with email %s is registered" % user_info.email)
    return user
