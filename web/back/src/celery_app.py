from celery import Celery


celery_app = Celery(
    "hyperspectrus",
    broker="amqp://guest:guest@rabbitmq:5672//",
    backend="redis://redis:6379/0"
)

celery_app.autodiscover_tasks([
    'src.tasks.session',
    ])

celery_app.conf.update(
    task_track_started=True,
    result_expires=3600
)
