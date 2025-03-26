from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth, OAuthError

from src.core.config import setting_conn, configure_logging, templates

router = APIRouter(prefix="/auth", tags=["auth"])

oauth = OAuth()
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=setting_conn.CLIENT_ID,
    client_secret=setting_conn.CLIENT_SECRET,
    client_kwargs={
        "scope": "email openid profile",
        "redirect_uri": "http://localhost:8000/auth/google",
    },
)


@router.get("/login/google")
async def login(request: Request):
    url = request.url_for("auth_google")
    return await oauth.google.authorize_redirect(request, url)


# @router.get('/auth')
@router.get("/google")
async def auth_google(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        return templates.TemplateResponse(
            name="error.html", context={"request": request, "error": e.error}
        )
    user = token.get("userinfo")
    if user:
        request.session["user"] = dict(user)
    return RedirectResponse("welcome")


@router.get("/logout")
def logout(request: Request):
    request.session.pop("user")
    request.session.clear()
    return RedirectResponse("/")


@router.get("/welcome")
def welcome(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/")
    return templates.TemplateResponse(
        name="welcome.html", context={"request": request, "user": user}
    )
