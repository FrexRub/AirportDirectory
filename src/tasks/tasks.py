import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

from starlette.templating import Jinja2Templates

from src.core.config import setting
from src.tasks.celery_conf import app

DIR_NAME = Path(__file__).parent.parent
templates = Jinja2Templates(directory=DIR_NAME / setting.templates_dir)


def generation_message_about_registration(name_user: str):
    message: str = (
        f"<div>"
        f'<h1 style="color: red;">Здравствуйте, {name_user}, '
        "вы успешно зарегистрировались на сайте airportcards.ru</h1>"
        "</div>"
    )
    return message


def generation_message_confirmation(token: str):
    template = templates.get_template(name="confirmation_email.html")
    confirmation_url = f"{setting.frontend_url}/users/register_confirm?token={token}"
    message = template.render(confirmation_url=confirmation_url)
    return message


@app.task(name="send_email_about_registration", bind=True, max_retries=3, default_retry_delay=5)
def send_email_about_registration(
    self, email_user: str, name_user: str, token: Optional[str] = None, topic: str = "info"
) -> None:
    """
    Отправка письма пользователю при регистрации
    topic = "info" - в случе уведомления о регистрации
    topic = "confirm" - в случе подтверждение регистрации
    """
    email = EmailMessage()
    email["From"] = setting.email_settings.smtp_user
    email["To"] = email_user

    if topic == "info":
        email["Subject"] = "Уведомление о регистрации"
        message = generation_message_about_registration(name_user)
    else:
        email["Subject"] = "Подтверждение регистрации"
        message = generation_message_confirmation(token=token)

    email.add_alternative(message, subtype="html")

    # with smtplib.SMTP_SSL(setting.email_settings.smtp_host, setting.email_settings.smtp_port) as server:
    with smtplib.SMTP(setting.email_settings.smtp_host, setting.email_settings.smtp_port) as server:
        try:
            server.starttls()
            server.login(
                setting.email_settings.smtp_user,
                setting.email_settings.smtp_password.get_secret_value(),
            )
            server.send_message(msg=email)
        except smtplib.SMTPException as exc:
            self.retry(exc=exc)
