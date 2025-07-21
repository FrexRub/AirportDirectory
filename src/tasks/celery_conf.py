from celery import Celery

from src.core.config import RedisSettings

redis_app = RedisSettings()

app = Celery(
    "tasks",
    broker=f"redis://{redis_app.redis_host}:{redis_app.redis_port}/1",
    backend=f"redis://{redis_app.redis_host}:{redis_app.redis_port}/1",
)

app.conf.update(
    result_expires=3600,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    broker_connection_retry_on_startup=True,  # повторное подключение
    task_acks_late=True,  # подтверждение задач по завершению
    task_reject_on_worker_lost=True,
)

app.conf.task_default_queue = "sendemail"

app.autodiscover_tasks(["src.tasks"])  # автоматическая загрузка задач
