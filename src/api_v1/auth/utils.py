import logging
import secrets
import urllib.parse

import aiohttp

# from authlib.integrations.starlette_client import OAuthError
# from fastapi import Request
from redis import Redis

from src.core.config import configure_logging, setting  # , oauth_yandex

# from src.core.exceptions import ExceptAuthentication

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


async def generate_google_oauth_redirect_uri(db_cache: Redis):
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


async def get_yandex_user_data(access_token):
    params = {"format": "json"}
    headers = {"Authorization": f"OAuth {access_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get("https://login.yandex.ru/info", params=params, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                response.raise_for_status()


# async def get_access_token(request: Request):
#     try:
#         token = await oauth_yandex.yandex.authorize_access_token(request)
#         # query_params = request.query_params
#     except OAuthError as exp:
#         logger.exception("Error authentication by Yandex.ID", exc_info=exp)
#         raise ExceptAuthentication(detail=exp)
#
#     return token
