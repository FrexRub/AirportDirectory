import logging
import smtplib
from email.message import EmailMessage

from celery import Celery

from src.core.config import configure_logging, setting_conn

celery = Celery("tasks", broker=f"redis://{setting_conn.REDIS_HOST}:{setting_conn.REDIS_PORT}")

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


def get_email_for_send(info_about_like: dict[str, str]):
    email = EmailMessage()
    email["Subject"] = "Ваше сообщение было лайкнуто"
    email["From"] = setting_conn.SMTP_USER
    email["To"] = info_about_like["email"]

    email.set_content(
        "<div>"
        f'<h1 style="color: red;">Здравствуйте, {info_about_like["name_user"]}, '
        f"ваш пост c на тему {info_about_like['title_post']} был отмечен  {info_about_like['name_friend']}</h1>"
        '<img src="https://static.vecteezy.com/system/resources/previews/008/295/031/original/custom-relationship'
        "-management-dashboard-ui-design-template-suitable-designing-application-for-android-and-ios-clean-style-app"
        '-mobile-free-vector.jpg" width="600">'
        "</div>",
        subtype="html",
    )
    return email


@celery.task(serializer="json")
def send_email(info_about_like: dict[str, str]):
    logger.info(f"Start send email to {info_about_like['email']}")
    email = get_email_for_send(info_about_like)
    with smtplib.SMTP(setting_conn.SMTP_HOST, setting_conn.SMTP_PORT) as server:
        try:
            server.starttls()
            server.login(setting_conn.SMTP_USER, setting_conn.SMTP_PASSWORD)
            server.send_message(email)
        except smtplib.SMTPException as exp:
            logger.exception(f"Error send mail, {exp}")
