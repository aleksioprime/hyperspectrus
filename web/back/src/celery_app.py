import os
from celery import Celery
from src.core.config import settings

broker_type = os.environ.get("CELERY_BROKER", "rabbitmq")

if broker_type == "rabbitmq":
    broker_url = f"{settings.rabbit.url}/"
    backend_url = f"{settings.redis.url}/0"
else:
    broker_url = f"{settings.redis.url}/1"
    backend_url = f"{settings.redis.url}/0"

celery_app = Celery(
    "hyperspectrus",
    broker=broker_url,
    backend=backend_url
)

celery_app.autodiscover_tasks([
    'src.tasks.session',
    ])

celery_app.conf.update(
    task_track_started=True,
    result_expires=3600
)
