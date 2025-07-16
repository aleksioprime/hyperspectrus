import os
import logging

from celery import Celery

from src.core.config import settings

logger = logging.getLogger("celery_app")
logging.basicConfig(level=logging.INFO)

broker_type = os.environ.get("CELERY_BROKER", "rabbitmq")

logger.info(f"CELERY_BROKER: {os.environ.get('CELERY_BROKER')}")
logger.info(f"broker_type: {broker_type}")
logger.info(f"settings.redis.url: {settings.redis.url}")
logger.info(f"settings.rabbit.url: {settings.rabbit.url}")

if broker_type == "rabbitmq":
    broker_url = f"{settings.rabbit.url}/"
    backend_url = f"{settings.redis.url}/0"
else:
    broker_url = f"{settings.redis.url}/1"
    backend_url = f"{settings.redis.url}/0"

logger.info(f"Final broker_url: {broker_url}")
logger.info(f"Final backend_url: {backend_url}")

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
