import logging

from fastapi import APIRouter, Request, Response, status
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth, OAuthError

from src.core.config import (
    setting_conn,
    configure_logging,
    templates,
    REDIRECT_URI,
    COOKIE_NAME,
)
from src.core.exceptions import CREDENTIALS_EXCEPTION
from src.core.jwt_utils import create_jwt, validate_password

router = APIRouter(prefix="/auth", tags=["auth"])

oauth = OAuth()
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=setting_conn.CLIENT_ID,
    client_secret=setting_conn.CLIENT_SECRET,
    client_kwargs={
        "scope": "email openid profile",
        "redirect_uri": REDIRECT_URI,
    },
)


configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


@router.get("/login/google")
async def login(request: Request):
    url = request.url_for("auth_google")
    return await oauth.google.authorize_redirect(request, url)


@router.get("/google")
async def auth_google(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        raise CREDENTIALS_EXCEPTION
        # return templates.TemplateResponse(
        #     name="error.html", context={"request": request, "error": e.error}
        # )
    # user_data = await oauth.google.parse_id_token(request, token)
    # user_email = user_data["email"]

    user = token.get("userinfo")
    logger.info(f"User info {user}")
    user_email = user.get("email")
    if user:
        request.session["user"] = dict(user)

    # access_token: str = create_jwt(str(user.id))
    access_token: str = await create_jwt(user_email)

    resp = RedirectResponse("welcome")
    # resp = Response(
    #     content="The user is logged in",
    #     status_code=status.HTTP_202_ACCEPTED,
    # )
    resp.set_cookie(key=COOKIE_NAME, value=access_token, httponly=True)
    return resp

    # return RedirectResponse("welcome")


@router.get("/logout")
def logout(request: Request):
    resp = RedirectResponse("/")
    resp.delete_cookie(COOKIE_NAME)
    request.session.pop("user")
    request.session.clear()
    return resp


@router.get("/welcome")
def welcome(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/")
    return templates.TemplateResponse(
        name="welcome.html", context={"request": request, "user": user}
    )
