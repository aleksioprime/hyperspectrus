from celery import Celery
from src.core.config import settings

celery_app = Celery(
    "hyperspectrus",
    broker=f"{settings.rabbit.url}/",
    backend=f"{settings.redis.url}/0"
)

celery_app.autodiscover_tasks([
    'src.tasks.session',
    ])

celery_app.conf.update(
    task_track_started=True,
    result_expires=3600
)
