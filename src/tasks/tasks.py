import logging
import smtplib
from email.message import EmailMessage

from src.core.config import configure_logging, setting_conn
from src.tasks.celery_conf import app

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


def generation_email_about_registration(email_user: str, name_user: str):
    email = EmailMessage()
    email["Subject"] = "Сообщение о регистрации"
    email["From"] = setting_conn.SMTP_USER
    email["To"] = email_user

    email.set_content(
        "<div>"
        f'<h1 style="color: red;">Здравствуйте, {name_user}, '
        f"вы успешно зарегистрировались на сайте airportcards.ru</h1>"
        "</div>",
        subtype="html",
    )
    return email


@app.task(name="send_email_about_registration", bind=True, max_retries=3, default_retry_delay=5)
def send_email_about_registration(self, topic: str, email_user: str, name_user: str):
    logger.info(f"Start send email to {email_user}")
    if topic == "info":
        email = generation_email_about_registration(email_user, name_user)
    else:
        logger.info("Не указана тема")
        return
    with smtplib.SMTP(setting_conn.SMTP_HOST, setting_conn.SMTP_PORT) as server:
        try:
            server.starttls()
            server.login(setting_conn.SMTP_USER, setting_conn.SMTP_PASSWORD)
            server.send_message(email)
        except smtplib.SMTPException as exc:
            logger.exception(f"Error send mail, {exc}")
            self.retry(exc=exc)
