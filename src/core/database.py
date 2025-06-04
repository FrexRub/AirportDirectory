from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from redis import asyncio as aioredis


from src.core.config import setting

engine = create_async_engine(
    url=setting.db.url,
    echo=setting.db.echo,
)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_redis_connection():
    redis = await aioredis.from_url(setting.redis.url, decode_responses=True)
    yield redis


async def get_cache_connection():
    redis_cash = aioredis.from_url(
        setting.redis.url + "/1",
        encoding="utf8",
        decode_responses=True,
    )
    yield redis_cash
