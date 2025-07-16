import logging
from pathlib import Path

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent.parent

DIR_LOGOTIP = "logotip"
DIR_FOTO = "foto"

COOKIE_NAME = "bonds_airport"
CACHE_EXP = 3600


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

    SECRET_KEY: str = "test"

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf8", extra="ignore")


setting_conn = SettingConn()  # type: ignore


class DbSetting(BaseSettings):
    url: str = (
        f"postgresql+asyncpg://"
        f"{setting_conn.postgres_user}:{setting_conn.postgres_password}"
        f"@{setting_conn.postgres_host}:{setting_conn.postgres_port}"
        f"/{setting_conn.postgres_db}"
    )
    echo: bool = False


class RedisSettings(BaseSettings):
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf8", extra="ignore")

    @property
    def url(self):
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


class EmailSettings(BaseSettings):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: SecretStr

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf8", extra="ignore")


class AuthJWT(BaseModel):
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1
    refresh_token_expire_minutes: int = 60 * 24 * 7


class Setting(BaseSettings):
    db: DbSetting = DbSetting()
    redis: RedisSettings = RedisSettings()
    email_settings: EmailSettings = EmailSettings()
    auth_jwt: AuthJWT = AuthJWT()


setting = Setting()
