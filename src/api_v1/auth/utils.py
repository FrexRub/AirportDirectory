import logging
import secrets
import urllib.parse

import aiohttp
from authlib.oauth2.rfc6749 import OAuth2Token
from redis import Redis

from src.core.config import configure_logging, setting
from src.core.exceptions import ExceptAuthentication

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


async def generate_google_oauth_redirect_uri(db_cache: Redis) -> str:
    """
    Генерация uri для редиректа, сохранения стэйта в БД Redis для подтверждения легитимности запроса
    """
    random_state = secrets.token_urlsafe(16)
    await db_cache.set(random_state, "state", ex=300)

    query_params = {
        "client_id": setting.google.OAUTH_GOOGLE_CLIENT_ID,
        "redirect_uri": setting.google.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(
            [
                "openid",
                "profile",
                "email",
            ]
        ),
        "state": random_state,
    }

    query_string = urllib.parse.urlencode(query_params, quote_via=urllib.parse.quote)
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    return f"{base_url}?{query_string}"


async def get_yandex_user_info(access_token: str) -> dict:
    """
    Получает информацию о пользователе от Yandex
    """
    async with aiohttp.ClientSession() as session:
        user_info_url = "https://login.yandex.ru/info"

        headers = {"Authorization": f"OAuth {access_token}", "Content-Type": "application/json"}

        params = {"format": "json"}

        async with session.get(user_info_url, headers=headers, params=params) as response:
            if response.status != 200:
                error_text = await response.text()
                raise ExceptAuthentication(detail=f"Yandex token error: {response.status}, {error_text}")

            return await response.json()


async def get_yandex_token(code: str) -> OAuth2Token:
    """
    Получает токен от Yandex OAuth используя код авторизации
    """
    async with aiohttp.ClientSession() as session:
        token_url = "https://oauth.yandex.ru/token"

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": setting.yandex.OAUTH_YANDEX_CLIENT_ID,
            "client_secret": setting.yandex.OAUTH_YANDEX_CLIENT_SECRET,
            "redirect_uri": setting.yandex.YANDEX_REDIRECT_URI,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with session.post(token_url, data=data, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                raise ExceptAuthentication(detail=f"Yandex token error: {response.status}, {error_text}")

            token_data = await response.json()
            return OAuth2Token(token_data)
