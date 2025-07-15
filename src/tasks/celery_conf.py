from celery import Celery

from src.core.config import setting_conn

app = Celery(
    "tasks",
    broker=f"redis://{setting_conn.REDIS_HOST}:{setting_conn.REDIS_PORT}/1",
    backend=f"redis://{setting_conn.REDIS_HOST}:{setting_conn.REDIS_PORT}/1",
)

app.conf.update(
    result_expires=3600,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
)
