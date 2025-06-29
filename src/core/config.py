import logging
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent.parent

DIR_LOGOTIP = "logotip"
DIR_FOTO = "foto"

COOKIE_NAME = "bonds_airport"
CACHE_EXP = 300  # 3600


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="[%(asctime)s.%(msecs)03d] %(module)10s:%(lineno)-3d %(levelname)-7s - %(message)s",
    )


class SettingConn(BaseSettings):
    postgres_user: str = "test"
    postgres_password: str = "test"
    postgres_db: str = "testdb"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    SECRET_KEY: str = "test"
    GOOGLE_CLIENT_ID: str = "test"
    GOOGLE_CLIENT_SECRET: str = "test"

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env")


setting_conn = SettingConn()  # type: ignore


class DbSetting(BaseSettings):
    url: str = (
        f"postgresql+asyncpg://"
        f"{setting_conn.postgres_user}:{setting_conn.postgres_password}"
        f"@{setting_conn.postgres_host}:{setting_conn.postgres_port}"
        f"/{setting_conn.postgres_db}"
    )
    echo: bool = False


class RedisSetting(BaseSettings):
    url: str = f"redis://{setting_conn.REDIS_HOST}:{setting_conn.REDIS_PORT}"


class AuthJWT(BaseModel):
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1
    refresh_token_expire_minutes: int = 60 * 24 * 7


class Setting(BaseSettings):
    db: DbSetting = DbSetting()
    redis: RedisSetting = RedisSetting()
    auth_jwt: AuthJWT = AuthJWT()


setting = Setting()
